"""
TORQ Routing Module

Deterministic routing overrides for real-time queries.
This module provides pattern-based routing that forces specific
execution paths without relying on keyword hints or LLM decisions.
"""

from .realtime_override import (
    RoutingOverride,
    detect_routing_override,
    FINANCE_TERMS,
    REALTIME_TERMS,
    NEWS_TERMS,
    LOOKUP_TERMS,
)

__all__ = [
    "RoutingOverride",
    "detect_routing_override",
    "FINANCE_TERMS",
    "REALTIME_TERMS",
    "NEWS_TERMS",
    "LOOKUP_TERMS",
]
