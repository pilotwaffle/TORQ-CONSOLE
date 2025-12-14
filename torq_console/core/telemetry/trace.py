"""
TORQ Console Distributed Tracing System.

Provides distributed tracing capabilities for agent runs with
router → model → tool → memory → finalize stages.
"""

import uuid
import time
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, AsyncContextManager, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import json

from .event import TorqEvent, TorqEventType


class SpanKind(str, Enum):
    """Span types for distributed tracing."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span status codes."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class TraceContext:
    """Context for trace propagation."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    flags: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for propagation."""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'baggage': self.baggage,
            'flags': self.flags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceContext':
        """Create context from dictionary."""
        return cls(**data)

    def child(self, span_id: Optional[str] = None) -> 'TraceContext':
        """Create a child context."""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=span_id or str(uuid.uuid4()),
            parent_span_id=self.span_id,
            baggage=self.baggage.copy(),
            flags=self.flags.copy()
        )


@dataclass
class TraceSpan:
    """A single span in a distributed trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str = ""
    kind: SpanKind = SpanKind.INTERNAL
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: SpanStatus = SpanStatus.UNSET
    status_message: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, Any]] = field(default_factory=dict)
    resource: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None

    def finish(self, end_time: Optional[datetime] = None, status: SpanStatus = SpanStatus.OK):
        """Finish the span."""
        self.end_time = end_time or datetime.utcnow()
        self.status = status
        if self.start_time and self.end_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def set_attribute(self, key: str, value: Any):
        """Set span attribute."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None, timestamp: Optional[datetime] = None):
        """Add event to span."""
        event = {
            'name': name,
            'timestamp': timestamp or datetime.utcnow(),
            'attributes': attributes or {}
        }
        self.events.append(event)

    def set_status(self, status: SpanStatus, message: str = ""):
        """Set span status."""
        self.status = status
        self.status_message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        data = {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'name': self.name,
            'kind': self.kind,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'status_message': self.status_message,
            'attributes': self.attributes,
            'events': [
                {
                    **event,
                    'timestamp': event['timestamp'].isoformat() if isinstance(event['timestamp'], datetime) else event['timestamp']
                }
                for event in self.events
            ],
            'links': self.links,
            'resource': self.resource,
            'duration_ms': self.duration_ms
        }
        return data


@dataclass
class TorqTrace:
    """A complete distributed trace."""
    trace_id: str
    root_span: Optional[TraceSpan] = None
    spans: List[TraceSpan] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    resource: Dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: TraceSpan):
        """Add a span to the trace."""
        self.spans.append(span)
        if self.root_span is None and span.parent_span_id is None:
            self.root_span = span

    def finish(self, end_time: Optional[datetime] = None, status: SpanStatus = SpanStatus.OK):
        """Finish the trace."""
        self.end_time = end_time or datetime.utcnow()
        self.status = status

    def get_span_by_id(self, span_id: str) -> Optional[TraceSpan]:
        """Get a span by its ID."""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None

    def get_child_spans(self, parent_span_id: str) -> List[TraceSpan]:
        """Get all child spans of a given span."""
        return [span for span in self.spans if span.parent_span_id == parent_span_id]

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            'trace_id': self.trace_id,
            'root_span': self.root_span.to_dict() if self.root_span else None,
            'spans': [span.to_dict() for span in self.spans],
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'attributes': self.attributes,
            'resource': self.resource,
            'span_count': len(self.spans),
            'duration_ms': (self.end_time - self.start_time).total_seconds() * 1000 if self.end_time else None
        }


class TraceManager:
    """Manages distributed traces and spans."""

    def __init__(self):
        self._active_traces: Dict[str, TorqTrace] = {}
        self._active_spans: Dict[str, TraceSpan] = {}
        self._trace_store: List[TorqTrace] = []
        self._max_stored_traces = 10000
        self._max_trace_age_hours = 24

    def create_trace(
        self,
        trace_id: Optional[str] = None,
        name: str = "",
        attributes: Optional[Dict[str, Any]] = None
    ) -> TorqTrace:
        """Create a new trace."""
        trace_id = trace_id or str(uuid.uuid4())
        trace = TorqTrace(
            trace_id=trace_id,
            attributes=attributes or {}
        )
        self._active_traces[trace_id] = trace
        return trace

    def create_span(
        self,
        trace_id: str,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        """Create a new span."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            raise ValueError(f"Trace {trace_id} not found")

        span_id = str(uuid.uuid4())
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            attributes=attributes or {}
        )

        trace.add_span(span)
        self._active_spans[span_id] = span
        return span

    def finish_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        message: str = ""
    ) -> Optional[TraceSpan]:
        """Finish a span."""
        span = self._active_spans.get(span_id)
        if span:
            span.set_status(status, message)
            span.finish()
            del self._active_spans[span_id]
        return span

    def finish_trace(
        self,
        trace_id: str,
        status: SpanStatus = SpanStatus.OK
    ) -> Optional[TorqTrace]:
        """Finish a trace."""
        trace = self._active_traces.get(trace_id)
        if trace:
            trace.finish(status=status)
            del self._active_traces[trace_id]
            self._store_trace(trace)
        return trace

    def get_trace(self, trace_id: str) -> Optional[TorqTrace]:
        """Get a trace by ID."""
        return self._active_traces.get(trace_id)

    def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """Get a span by ID."""
        return self._active_spans.get(span_id)

    def list_active_traces(self) -> List[str]:
        """List all active trace IDs."""
        return list(self._active_traces.keys())

    def list_active_spans(self) -> List[str]:
        """List all active span IDs."""
        return list(self._active_spans.keys())

    def create_span_context(
        self,
        trace_id: str,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None
    ) -> TraceContext:
        """Create a trace context for propagation."""
        return TraceContext(
            trace_id=trace_id,
            span_id=span_id or str(uuid.uuid4()),
            parent_span_id=parent_span_id
        )

    @asynccontextmanager
    async def start_span(
        self,
        trace_id: str,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Async context manager for creating and auto-finishing spans."""
        span = self.create_span(
            trace_id=trace_id,
            name=name,
            kind=kind,
            parent_span_id=parent_span_id,
            attributes=attributes
        )
        try:
            yield span
            self.finish_span(span.span_id, SpanStatus.OK)
        except Exception as e:
            span.set_attribute('error', str(e))
            span.add_event('exception', {'error': str(e)})
            self.finish_span(span.span_id, SpanStatus.ERROR, str(e))
            raise

    def _store_trace(self, trace: TorqTrace):
        """Store a completed trace."""
        self._trace_store.append(trace)
        self._cleanup_old_traces()

    def _cleanup_old_traces(self):
        """Clean up old traces to prevent memory leaks."""
        current_time = datetime.utcnow()

        # Remove traces by age
        cutoff_time = current_time - timedelta(hours=self._max_trace_age_hours)
        self._trace_store = [
            trace for trace in self._trace_store
            if trace.end_time and trace.end_time > cutoff_time
        ]

        # Remove excess traces by count
        if len(self._trace_store) > self._max_stored_traces:
            self._trace_store = self._trace_store[-self._max_stored_traces:]

    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get trace manager statistics."""
        return {
            'active_traces': len(self._active_traces),
            'active_spans': len(self._active_spans),
            'stored_traces': len(self._trace_store),
            'max_stored_traces': self._max_stored_traces,
            'max_trace_age_hours': self._max_trace_age_hours
        }


# Global trace manager instance
_global_trace_manager: Optional[TraceManager] = None


def get_trace_manager() -> TraceManager:
    """Get the global trace manager instance."""
    global _global_trace_manager
    if _global_trace_manager is None:
        _global_trace_manager = TraceManager()
    return _global_trace_manager


# Trace decorators
def trace_agent_run(trace_manager: Optional[TraceManager] = None):
    """Decorator for tracing agent runs."""
    manager = trace_manager or get_trace_manager()

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            # Extract run_id from kwargs or create new one
            run_id = kwargs.get('run_id') or str(uuid.uuid4())
            trace_id = kwargs.get('trace_id') or str(uuid.uuid4())

            # Create trace
            trace = manager.create_trace(
                trace_id=trace_id,
                name=f"agent_run_{func.__name__}",
                attributes={
                    'function': func.__name__,
                    'run_id': run_id,
                    'agent_name': kwargs.get('agent_name', 'unknown'),
                    'agent_type': kwargs.get('agent_type', 'unknown')
                }
            )

            # Create main span
            span = manager.create_span(
                trace_id=trace_id,
                name=f"agent_execution_{func.__name__}",
                kind=SpanKind.INTERNAL,
                attributes={
                    'module': func.__module__,
                    'function': func.__name__
                }
            )

            try:
                # Add context to kwargs
                kwargs['_trace_context'] = manager.create_span_context(
                    trace_id=trace_id,
                    span_id=span.span_id
                )
                kwargs['_trace_id'] = trace_id

                # Execute function
                result = await func(*args, **kwargs)

                # Finish successfully
                manager.finish_span(span.span_id, SpanStatus.OK)
                manager.finish_trace(trace_id, SpanStatus.OK)

                return result

            except Exception as e:
                # Handle error
                span.set_attribute('error', str(e))
                span.add_event('exception', {'error': str(e)})
                manager.finish_span(span.span_id, SpanStatus.ERROR, str(e))
                manager.finish_trace(trace_id, SpanStatus.ERROR)
                raise

        def sync_wrapper(*args, **kwargs):
            # For sync functions, create a simple span
            run_id = kwargs.get('run_id') or str(uuid.uuid4())
            trace_id = kwargs.get('trace_id') or str(uuid.uuid4())

            trace = manager.create_trace(
                trace_id=trace_id,
                name=f"agent_run_{func.__name__}",
                attributes={
                    'function': func.__name__,
                    'run_id': run_id
                }
            )

            span = manager.create_span(
                trace_id=trace_id,
                name=f"agent_execution_{func.__name__}",
                attributes={'function': func.__name__}
            )

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                span.set_attribute('execution_time_ms', (time.time() - start_time) * 1000)
                manager.finish_span(span.span_id, SpanStatus.OK)
                manager.finish_trace(trace_id, SpanStatus.OK)
                return result
            except Exception as e:
                span.set_attribute('error', str(e))
                manager.finish_span(span.span_id, SpanStatus.ERROR, str(e))
                manager.finish_trace(trace_id, SpanStatus.ERROR)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def trace_tool_execution(trace_manager: Optional[TraceManager] = None):
    """Decorator for tracing tool executions."""
    manager = trace_manager or get_trace_manager()

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            # Get trace context
            trace_context = kwargs.get('_trace_context')
            if not trace_context:
                # No active trace, skip tracing
                return await func(*args, **kwargs)

            # Create tool span
            span = manager.create_span(
                trace_id=trace_context.trace_id,
                name=f"tool_execution_{func.__name__}",
                kind=SpanKind.INTERNAL,
                parent_span_id=trace_context.span_id,
                attributes={
                    'tool_name': kwargs.get('tool_name', func.__name__),
                    'tool_type': kwargs.get('tool_type', 'unknown'),
                    'parameters': {k: v for k, v in kwargs.items() if k != '_trace_context'}
                }
            )

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                span.set_attribute('execution_time_ms', execution_time)
                span.set_attribute('success', True)
                manager.finish_span(span.span_id, SpanStatus.OK)
                return result
            except Exception as e:
                span.set_attribute('error', str(e))
                span.set_attribute('execution_time_ms', (time.time() - start_time) * 1000)
                manager.finish_span(span.span_id, SpanStatus.ERROR, str(e))
                raise

        return async_wrapper
    return decorator


def trace_model_interaction(trace_manager: Optional[TraceManager] = None):
    """Decorator for tracing model interactions."""
    manager = trace_manager or get_trace_manager()

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            # Get trace context
            trace_context = kwargs.get('_trace_context')
            if not trace_context:
                return await func(*args, **kwargs)

            # Extract model info
            model_provider = kwargs.get('model_provider', 'unknown')
            model_name = kwargs.get('model_name', 'unknown')
            prompt_tokens = kwargs.get('prompt_tokens', 0)

            # Create model span
            span = manager.create_span(
                trace_id=trace_context.trace_id,
                name=f"model_interaction_{model_name}",
                kind=SpanKind.CLIENT,
                parent_span_id=trace_context.span_id,
                attributes={
                    'model_provider': model_provider,
                    'model_name': model_name,
                    'prompt_tokens': prompt_tokens,
                    'temperature': kwargs.get('temperature'),
                    'max_tokens': kwargs.get('max_tokens')
                }
            )

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000
                span.set_attribute('response_time_ms', response_time)
                span.set_attribute('success', True)

                # Try to extract token usage from result
                if hasattr(result, 'usage'):
                    span.set_attribute('completion_tokens', getattr(result.usage, 'completion_tokens', 0))
                    span.set_attribute('total_tokens', getattr(result.usage, 'total_tokens', 0))

                manager.finish_span(span.span_id, SpanStatus.OK)
                return result
            except Exception as e:
                span.set_attribute('error', str(e))
                span.set_attribute('response_time_ms', (time.time() - start_time) * 1000)
                manager.finish_span(span.span_id, SpanStatus.ERROR, str(e))
                raise

        return async_wrapper
    return decorator


def trace_memory_operation(trace_manager: Optional[TraceManager] = None):
    """Decorator for tracing memory operations."""
    manager = trace_manager or get_trace_manager()

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            # Get trace context
            trace_context = kwargs.get('_trace_context')
            if not trace_context:
                return await func(*args, **kwargs)

            # Extract memory info
            memory_type = kwargs.get('memory_type', 'unknown')
            operation_type = kwargs.get('operation_type', 'unknown')

            # Create memory span
            span = manager.create_span(
                trace_id=trace_context.trace_id,
                name=f"memory_operation_{operation_type}",
                kind=SpanKind.INTERNAL,
                parent_span_id=trace_context.span_id,
                attributes={
                    'memory_type': memory_type,
                    'operation_type': operation_type,
                    'key': kwargs.get('key'),
                    'keys': kwargs.get('keys', [])
                }
            )

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                operation_time = (time.time() - start_time) * 1000
                span.set_attribute('operation_time_ms', operation_time)
                span.set_attribute('success', True)
                manager.finish_span(span.span_id, SpanStatus.OK)
                return result
            except Exception as e:
                span.set_attribute('error', str(e))
                span.set_attribute('operation_time_ms', (time.time() - start_time) * 1000)
                manager.finish_span(span.span_id, SpanStatus.ERROR, str(e))
                raise

        return async_wrapper
    return decorator


def trace_routing_decision(trace_manager: Optional[TraceManager] = None):
    """Decorator for tracing routing decisions."""
    manager = trace_manager or get_trace_manager()

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            # Get trace context
            trace_context = kwargs.get('_trace_context')
            if not trace_context:
                return await func(*args, **kwargs)

            # Create routing span
            span = manager.create_span(
                trace_id=trace_context.trace_id,
                name="routing_decision",
                kind=SpanKind.INTERNAL,
                parent_span_id=trace_context.span_id,
                attributes={
                    'query': kwargs.get('query', '')[:100],  # Truncate for privacy
                    'query_type': kwargs.get('query_type'),
                    'routing_strategy': kwargs.get('routing_strategy', 'unknown')
                }
            )

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                routing_time = (time.time() - start_time) * 1000
                span.set_attribute('routing_time_ms', routing_time)

                # Add routing result details
                if hasattr(result, 'selected_agent'):
                    span.set_attribute('selected_agent', result.selected_agent)
                if hasattr(result, 'confidence_score'):
                    span.set_attribute('confidence_score', result.confidence_score)
                if hasattr(result, 'candidate_agents'):
                    span.set_attribute('candidate_agents', result.candidate_agents)

                manager.finish_span(span.span_id, SpanStatus.OK)
                return result
            except Exception as e:
                span.set_attribute('error', str(e))
                span.set_attribute('routing_time_ms', (time.time() - start_time) * 1000)
                manager.finish_span(span.span_id, SpanStatus.ERROR, str(e))
                raise

        return async_wrapper
    return decorator