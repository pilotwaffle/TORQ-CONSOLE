"""
TORQ Console - FastAPI Middleware for OpenTelemetry Tracing

Automatically traces all incoming requests with proper span propagation.
Integrates with Railway/FastAPI backend.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time

from .tracing import (
    TORQTracer,
    get_tracer,
    SpanKind,
    TraceContext
)


class TracingMiddleware(BaseHTTPMiddleware):
    """
    OpenTelemetry tracing middleware for FastAPI.

    Automatically creates spans for all HTTP requests with:
    - Trace context extraction from headers
    - Span propagation to downstream services
    - Standard attributes (method, route, status, latency)
    """

    def __init__(
        self,
        app: ASGIApp,
        service_name: str = "torq-console",
        otlp_endpoint: str = None
    ):
        super().__init__(app)
        self.tracer = get_tracer(
            service_name=service_name,
            otlp_endpoint=otlp_endpoint
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract trace context from incoming headers
        trace_context = self._extract_trace_context(request)

        # Create span for API request
        span_name = f"{request.method.value} {request.url.path}"
        span = self.tracer.start_span(
            name=span_name,
            kind=SpanKind.API_REQUEST,
            context=trace_context,
            attributes={
                "http.method": request.method.value,
                "http.route": request.url.path,
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname,
                "http.target": request.url.query or "",
                "http.user_agent": request.headers.get("user-agent", ""),
                "http.client_ip": self._get_client_ip(request)
            }
        )

        # Store context in request state for downstream access
        request.state.trace_context = trace_context
        request.state.trace_span = span

        start_time = time.time()

        try:
            response = await call_next(request)

            # Record response attributes
            span.attributes.update({
                "http.status_code": response.status_code,
                "http.status_text": response.reason_phrase or ""
            })

            return response

        except Exception as exc:
            # Record error in span
            span.status = f"error: {exc}"
            span.events.append({
                "name": "exception",
                "timestamp": time.time(),
                "attributes": {
                    "exception.type": type(exc).__name__,
                    "exception.message": str(exc)
                }
            })
            raise

        finally:
            # Finalize span
            end_time = time.time()
            span.end_time = end_time
            span.attributes["http.latency_ms"] = (end_time - start_time) * 1000

            if self.tracer.enable_console:
                print(f"[TRACE] {span.to_dict()}")

    def _extract_trace_context(self, request: Request) -> TraceContext:
        """Extract trace context from request headers"""
        headers = dict(request.headers)

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

        # Generate new context if none found
        return TraceContext.generate()

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

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to client host
        if request.client:
            return request.client.host

        return "unknown"


# Convenience function to add tracing to FastAPI app
def add_tracing_middleware(
    app,
    service_name: str = "torq-console",
    otlp_endpoint: str = None
):
    """
    Add OpenTelemetry tracing middleware to FastAPI app.

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> add_tracing_middleware(app, service_name="torq-api")
    """
    app.add_middleware(TracingMiddleware, service_name=service_name, otlp_endpoint=otlp_endpoint)
    return app


__all__ = ["TracingMiddleware", "add_tracing_middleware"]
