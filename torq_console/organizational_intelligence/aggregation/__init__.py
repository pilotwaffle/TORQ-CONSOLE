"""
TORQ Layer 9 - Cross-Mission Intelligence Aggregation

L9-M1: Aggregates intelligence across missions for organizational learning.
"""

from .cross_mission_aggregator import (
    CrossMissionAggregator,
    MissionGrouping,
    CrossMissionAggregation,
    get_cross_mission_aggregator,
)

__all__ = [
    "CrossMissionAggregator",
    "MissionGrouping",
    "CrossMissionAggregation",
    "get_cross_mission_aggregator",
]
