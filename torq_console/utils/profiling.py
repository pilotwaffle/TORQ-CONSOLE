"""
Structured profiling utilities for TORQ Console.

Provides lightweight timing decorators and structured JSON logging
for performance monitoring and optimization.
"""

import functools
import time
import logging
import json
from typing import Callable, Any, Dict, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """
    Lightweight performance profiler with structured JSON logging.

    Optimization: Minimal overhead timing decorators with structured
    output for easy parsing and analysis.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def profile(self, operation_name: Optional[str] = None):
        """
        Decorator for profiling function execution time.

        Usage:
            profiler = PerformanceProfiler()

            @profiler.profile("database_query")
            def query_database():
                ...

            @profiler.profile()  # Uses function name
            async def async_operation():
                ...

        Args:
            operation_name: Name for the operation (defaults to function name)
        """
        def decorator(func: Callable) -> Callable:
            name = operation_name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                start_time = time.perf_counter()
                start_timestamp = datetime.now().isoformat()
                exception_occurred = None

                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    exception_occurred = type(e).__name__
                    raise
                finally:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000

                    # Emit structured JSON log
                    log_entry = {
                        "event": "performance_metric",
                        "operation": name,
                        "duration_ms": round(elapsed_ms, 2),
                        "timestamp": start_timestamp,
                        "success": exception_occurred is None,
                        "exception": exception_occurred
                    }

                    logger.info(json.dumps(log_entry))

                    # Track metrics
                    if name not in self.metrics:
                        self.metrics[name] = {
                            "count": 0,
                            "total_ms": 0.0,
                            "min_ms": float('inf'),
                            "max_ms": 0.0,
                            "errors": 0
                        }

                    metrics = self.metrics[name]
                    metrics["count"] += 1
                    metrics["total_ms"] += elapsed_ms
                    metrics["min_ms"] = min(metrics["min_ms"], elapsed_ms)
                    metrics["max_ms"] = max(metrics["max_ms"], elapsed_ms)
                    if exception_occurred:
                        metrics["errors"] += 1

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start_time = time.perf_counter()
                start_timestamp = datetime.now().isoformat()
                exception_occurred = None

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    exception_occurred = type(e).__name__
                    raise
                finally:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000

                    # Emit structured JSON log
                    log_entry = {
                        "event": "performance_metric",
                        "operation": name,
                        "duration_ms": round(elapsed_ms, 2),
                        "timestamp": start_timestamp,
                        "success": exception_occurred is None,
                        "exception": exception_occurred
                    }

                    logger.info(json.dumps(log_entry))

                    # Track metrics
                    if name not in self.metrics:
                        self.metrics[name] = {
                            "count": 0,
                            "total_ms": 0.0,
                            "min_ms": float('inf'),
                            "max_ms": 0.0,
                            "errors": 0
                        }

                    metrics = self.metrics[name]
                    metrics["count"] += 1
                    metrics["total_ms"] += elapsed_ms
                    metrics["min_ms"] = min(metrics["min_ms"], elapsed_ms)
                    metrics["max_ms"] = max(metrics["max_ms"], elapsed_ms)
                    if exception_occurred:
                        metrics["errors"] += 1

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregated performance metrics.

        Returns:
            Dictionary of metrics by operation name with statistics
        """
        result = {}
        for name, metrics in self.metrics.items():
            result[name] = {
                "count": metrics["count"],
                "total_ms": round(metrics["total_ms"], 2),
                "avg_ms": round(metrics["total_ms"] / max(1, metrics["count"]), 2),
                "min_ms": round(metrics["min_ms"], 2) if metrics["min_ms"] != float('inf') else 0,
                "max_ms": round(metrics["max_ms"], 2),
                "errors": metrics["errors"],
                "error_rate": round(metrics["errors"] / max(1, metrics["count"]) * 100, 1)
            }
        return result

    def reset_metrics(self):
        """Reset all collected metrics."""
        self.metrics.clear()

    def emit_summary(self):
        """Emit a structured JSON summary of all metrics."""
        summary = {
            "event": "performance_summary",
            "timestamp": datetime.now().isoformat(),
            "metrics": self.get_metrics()
        }
        logger.info(json.dumps(summary))


class TimingContext:
    """
    Context manager for timing code blocks.

    Usage:
        profiler = PerformanceProfiler()

        with profiler.timing("expensive_operation"):
            # code to time
            ...

        # Or async
        async with profiler.timing("async_operation"):
            await expensive_async_call()
    """

    def __init__(self, profiler: PerformanceProfiler, operation_name: str):
        self.profiler = profiler
        self.operation_name = operation_name
        self.start_time = None
        self.start_timestamp = None

    def __enter__(self):
        if self.profiler.enabled:
            self.start_time = time.perf_counter()
            self.start_timestamp = datetime.now().isoformat()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.profiler.enabled:
            return

        elapsed_ms = (time.perf_counter() - self.start_time) * 1000

        # Emit structured JSON log
        log_entry = {
            "event": "performance_metric",
            "operation": self.operation_name,
            "duration_ms": round(elapsed_ms, 2),
            "timestamp": self.start_timestamp,
            "success": exc_type is None,
            "exception": exc_type.__name__ if exc_type else None
        }

        logger.info(json.dumps(log_entry))

    async def __aenter__(self):
        if self.profiler.enabled:
            self.start_time = time.perf_counter()
            self.start_timestamp = datetime.now().isoformat()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.profiler.enabled:
            return

        elapsed_ms = (time.perf_counter() - self.start_time) * 1000

        # Emit structured JSON log
        log_entry = {
            "event": "performance_metric",
            "operation": self.operation_name,
            "duration_ms": round(elapsed_ms, 2),
            "timestamp": self.start_timestamp,
            "success": exc_type is None,
            "exception": exc_type.__name__ if exc_type else None
        }

        logger.info(json.dumps(log_entry))


# Add timing method to PerformanceProfiler
PerformanceProfiler.timing = lambda self, operation_name: TimingContext(self, operation_name)


# Global profiler instance
_global_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    return _global_profiler


def profile(operation_name: Optional[str] = None):
    """
    Decorator for profiling using the global profiler.

    Usage:
        from torq_console.utils.profiling import profile

        @profile("my_operation")
        def my_function():
            ...

        @profile()  # Uses function name
        async def my_async_function():
            ...
    """
    return _global_profiler.profile(operation_name)


def timing(operation_name: str):
    """
    Context manager for timing using the global profiler.

    Usage:
        from torq_console.utils.profiling import timing

        with timing("expensive_operation"):
            # code to time
            ...
    """
    return _global_profiler.timing(operation_name)


def get_metrics() -> Dict[str, Dict[str, Any]]:
    """Get metrics from the global profiler."""
    return _global_profiler.get_metrics()


def emit_summary():
    """Emit a summary from the global profiler."""
    _global_profiler.emit_summary()


def reset_metrics():
    """Reset metrics in the global profiler."""
    _global_profiler.reset_metrics()
