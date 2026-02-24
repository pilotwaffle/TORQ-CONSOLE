"""
Telemetry Sink Abstraction

Clean separation of telemetry storage from request handling.
Tests can use InMemorySink; production uses SupabaseSink.

Usage:
    from torq_console.telemetry.sinks import get_telemetry_sink

    sink = get_telemetry_sink()
    await sink.write_trace(trace, spans)
"""

import logging
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from pydantic import BaseModel


class TelemetryWriteResult(BaseModel):
    """Result of a telemetry write operation."""
    success: bool
    storage: str
    trace_id: str
    spans_written: int
    error: Optional[str] = None


class TelemetrySink(ABC):
    """
    Abstract base class for telemetry storage backends.

    All telemetry writes go through this interface.
    Tests can use InMemorySink; production uses SupabaseSink.
    """

    @abstractmethod
    async def write_trace(
        self,
        trace: Dict[str, Any],
        spans: Optional[List[Dict[str, Any]]] = None,
    ) -> TelemetryWriteResult:
        """
        Write a telemetry trace to storage.

        Args:
            trace: Trace data
            spans: Optional list of spans

        Returns:
            TelemetryWriteResult with success status
        """
        ...

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the sink is healthy."""
        ...

    @abstractmethod
    def get_storage_type(self) -> str:
        """Return storage type identifier (e.g., 'supabase', 'memory', 'null')."""
        ...


class InMemorySink(TelemetrySink):
    """
    In-memory telemetry sink for testing.

    Stores traces in a list (no persistence).
    Never fails due to network/storage issues.
    """

    def __init__(self):
        self.traces: List[Dict[str, Any]] = []
        self.spans: List[Dict[str, Any]] = []

    async def write_trace(
        self,
        trace: Dict[str, Any],
        spans: Optional[List[Dict[str, Any]]] = None,
    ) -> TelemetryWriteResult:
        """Store trace in memory."""
        self.traces.append(trace)
        if spans:
            self.spans.extend(spans)

        return TelemetryWriteResult(
            success=True,
            storage="memory",
            trace_id=trace.get("trace_id", "unknown"),
            spans_written=len(spans) if spans else 0,
        )

    async def health_check(self) -> Dict[str, Any]:
        """In-memory sink is always healthy."""
        return {
            "storage": "memory",
            "healthy": True,
            "traces_stored": len(self.traces),
            "spans_stored": len(self.spans),
        }

    def get_storage_type(self) -> str:
        return "memory"


class NullSink(TelemetrySink):
    """
    Null telemetry sink that discards all telemetry.

    Use when telemetry is completely disabled.
    Never fails and never stores anything.
    """

    async def write_trace(
        self,
        trace: Dict[str, Any],
        spans: Optional[List[Dict[str, Any]]] = None,
    ) -> TelemetryWriteResult:
        """Discard trace."""
        return TelemetryWriteResult(
            success=True,
            storage="null",
            trace_id=trace.get("trace_id", "unknown"),
            spans_written=0,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Null sink is always healthy."""
        return {
            "storage": "null",
            "healthy": True,
            "traces_stored": 0,
            "spans_stored": 0,
        }

    def get_storage_type(self) -> str:
        return "null"


class SupabaseSink(TelemetrySink):
    """
    Supabase telemetry sink for production.

    Writes to Supabase telemetry tables with best-effort error handling.
    """

    def __init__(self):
        self.storage_type = "supabase"
        self.logger = logging.getLogger(__name__)

    async def write_trace(
        self,
        trace: Dict[str, Any],
        spans: Optional[List[Dict[str, Any]]] = None,
    ) -> TelemetryWriteResult:
        """Write trace to Supabase."""
        try:
            from torq_console.telemetry import supabase_ingest

            await supabase_ingest(trace, spans or [])

            return TelemetryWriteResult(
                success=True,
                storage="supabase",
                trace_id=trace.get("trace_id", "unknown"),
                spans_written=len(spans) if spans else 0,
            )

        except Exception as e:
            self.logger.error(f"SupabaseSink write failed: {e}")
            return TelemetryWriteResult(
                success=False,
                storage="supabase",
                trace_id=trace.get("trace_id", "unknown"),
                spans_written=0,
                error=str(e),
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase connectivity."""
        try:
            from torq_console.telemetry import get_telemetry_health
            return await get_telemetry_health()
        except Exception as e:
            return {
                "storage": "supabase",
                "healthy": False,
                "error": str(e),
            }

    def get_storage_type(self) -> str:
        return "supabase"


# Default sink based on environment
_default_sink: Optional[TelemetrySink] = None


def get_telemetry_sink() -> TelemetrySink:
    """
    Get the appropriate telemetry sink based on environment.

    Priority:
    1. TORQ_TELEMETRY_SINK environment variable (explicit)
    2. SupabaseSink if configured and enabled
    3. InMemorySink for testing
    4. NullSink if explicitly disabled
    """
    global _default_sink

    if _default_sink is not None:
        return _default_sink

    import os

    # Check for explicit sink selection
    sink_type = os.environ.get("TORQ_TELEMETRY_SINK", "").lower()

    if sink_type == "null":
        _default_sink = NullSink()
        return _default_sink

    if sink_type == "memory":
        _default_sink = InMemorySink()
        return _default_sink

    # Check if telemetry is enabled
    telemetry_enabled = os.environ.get("TORQ_TELEMETRY_ENABLED", "true").lower() == "true"

    if not telemetry_enabled:
        _default_sink = NullSink()
        return _default_sink

    # Default to Supabase
    _default_sink = SupabaseSink()
    return _default_sink


def reset_telemetry_sink():
    """Reset the telemetry sink (mainly for testing)."""
    global _default_sink
    _default_sink = None
