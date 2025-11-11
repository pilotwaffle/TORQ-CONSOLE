"""
Centralized thread pool management for TORQ Console.

Prevents thread oversubscription by sharing a limited thread pool
across all modules instead of creating multiple independent executors.

Usage:
    from torq_console.core.executor_pool import get_executor

    executor = get_executor()
    future = executor.submit(blocking_function, *args)
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import os

# Global shared executor
_shared_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = None

logger = logging.getLogger(__name__)


def get_max_workers() -> int:
    """
    Calculate optimal thread pool size.

    Uses CPU count * 2 as baseline, capped at 16 to prevent oversubscription.
    Can be overridden with TORQ_MAX_WORKERS environment variable.
    """
    if env_workers := os.getenv('TORQ_MAX_WORKERS'):
        try:
            return int(env_workers)
        except ValueError:
            logger.warning(f"Invalid TORQ_MAX_WORKERS value: {env_workers}, using default")

    # CPU count * 2, capped at 16
    try:
        cpu_count = os.cpu_count() or 4
        return min(cpu_count * 2, 16)
    except Exception:
        return 8  # Reasonable default


def get_executor() -> ThreadPoolExecutor:
    """
    Get the shared thread pool executor.

    Creates executor on first call. Thread-safe via import lock.
    All modules should use this instead of creating their own executors.

    Returns:
        Shared ThreadPoolExecutor instance
    """
    global _shared_executor

    if _shared_executor is None:
        max_workers = get_max_workers()
        _shared_executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="torq_shared"
        )
        logger.info(f"Created shared thread pool with {max_workers} workers")

    return _shared_executor


def shutdown_executor(wait: bool = True) -> None:
    """
    Shutdown the shared executor.

    Should be called during application shutdown.

    Args:
        wait: If True, wait for all pending tasks to complete
    """
    global _shared_executor

    if _shared_executor is not None:
        logger.info("Shutting down shared thread pool")
        _shared_executor.shutdown(wait=wait)
        _shared_executor = None


def get_executor_stats() -> dict:
    """
    Get statistics about the shared executor.

    Returns:
        Dictionary with executor statistics
    """
    if _shared_executor is None:
        return {
            "initialized": False,
            "max_workers": 0,
            "active": False
        }

    return {
        "initialized": True,
        "max_workers": _shared_executor._max_workers,
        "active": not _shared_executor._shutdown,
        "thread_name_prefix": "torq_shared"
    }
