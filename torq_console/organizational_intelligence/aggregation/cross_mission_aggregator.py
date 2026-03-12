"""
TORQ Layer 9 - Cross-Mission Intelligence Aggregator

L9-M1: Aggregates intelligence across missions for organizational learning.

The CrossMissionAggregator groups missions by various dimensions
and generates organization-level intelligence.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4
from collections import defaultdict

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import models
from ..models import (
    MissionGrouping,
    CrossMissionAggregation,
)


# ============================================================================
# Mission Summary for Aggregation
# ============================================================================

class MissionSummary(BaseModel):
    """Summary of a mission for aggregation."""
    mission_id: str
    mission_type: str
    domain: Optional[str] = None
    workflow: Optional[str] = None
    agent_route: Optional[str] = None

    # Outcome
    success: bool = False
    success_score: float = 0.0
    quality_score: float = 0.0

    # Performance
    duration_seconds: float = 0.0
    token_count: int = 0
    tool_calls: int = 0

    # Readiness
    readiness_state: Optional[str] = None

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


# ============================================================================
# Cross-Mission Aggregator
# ============================================================================

class CrossMissionAggregator:
    """
    Aggregates intelligence across multiple missions.

    Groups missions by type, domain, workflow, etc. and
    generates organization-level insights.
    """

    def __init__(self):
        """Initialize the aggregator."""
        # Mission storage
        self._mission_summaries: Dict[str, MissionSummary] = {}

        # Aggregation cache
        self._cached_aggregations: Dict[str, CrossMissionAggregation] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=15)

    def add_mission_summary(self, summary: MissionSummary) -> None:
        """
        Add a mission summary for aggregation.

        Args:
            summary: MissionSummary to add
        """
        self._mission_summaries[summary.mission_id] = summary
        logger.debug(
            f"[CrossMissionAggregator] Added mission {summary.mission_id}: "
            f"type={summary.mission_type}, success={summary.success}"
        )

    async def aggregate_by_mission_type(
        self,
        mission_type: str,
    ) -> CrossMissionAggregation:
        """
        Aggregate missions by type.

        Args:
            mission_type: Mission type to aggregate

        Returns:
            CrossMissionAggregation with results
        """
        # Filter missions by type
        missions = [
            m for m in self._mission_summaries.values()
            if m.mission_type == mission_type
        ]

        if not missions:
            return CrossMissionAggregation(
                aggregation_type="by_mission_type",
                groupings=[],
                total_missions_analyzed=0,
                overall_success_rate=0.0,
            )

        # Calculate metrics
        total = len(missions)
        successful = sum(1 for m in missions if m.success)
        success_rate = successful / total if total > 0 else 0.0

        # Create grouping
        grouping = MissionGrouping(
            grouping_id=f"type_{mission_type}",
            grouping_type="mission_type",
            grouping_key=mission_type,
            mission_ids=[m.mission_id for m in missions],
            total_missions=total,
            success_count=successful,
            success_rate=success_rate,
            avg_duration=sum(m.duration_seconds for m in missions) / total,
            avg_quality_score=sum(m.quality_score for m in missions) / total,
            timeframe_start=min(m.started_at for m in missions),
            timeframe_end=max(m.completed_at for m in missions),
        )

        # Identify strategic signals
        strategic_signals = []
        if success_rate > 0.8:
            strategic_signals.append("high_success_rate")
        if success_rate < 0.5:
            strategic_signals.append("low_success_rate")
        if grouping.avg_duration > 300:
            strategic_signals.append("long_execution_times")

        return CrossMissionAggregation(
            aggregation_id=str(uuid4()),
            aggregation_type="by_mission_type",
            groupings=[grouping],
            total_missions_analyzed=total,
            overall_success_rate=success_rate,
            strategic_signals=strategic_signals,
        )

    async def aggregate_by_domain(
        self,
        domain: str,
    ) -> CrossMissionAggregation:
        """
        Aggregate missions by domain.

        Args:
            domain: Domain to aggregate

        Returns:
            CrossMissionAggregation with results
        """
        # Filter missions by domain
        missions = [
            m for m in self._mission_summaries.values()
            if m.domain == domain
        ]

        if not missions:
            return CrossMissionAggregation(
                aggregation_type="by_domain",
                groupings=[],
                total_missions_analyzed=0,
                overall_success_rate=0.0,
            )

        # Calculate metrics
        total = len(missions)
        successful = sum(1 for m in missions if m.success)
        success_rate = successful / total if total > 0 else 0.0

        # Find common patterns
        workflows = defaultdict(int)
        for m in missions:
            if m.workflow:
                workflows[m.workflow] += 1

        common_workflows = [w for w, c in workflows.items() if c >= 2]

        grouping = MissionGrouping(
            grouping_id=f"domain_{domain}",
            grouping_type="domain",
            grouping_key=domain,
            mission_ids=[m.mission_id for m in missions],
            total_missions=total,
            success_count=successful,
            success_rate=success_rate,
            avg_duration=sum(m.duration_seconds for m in missions) / total,
            avg_quality_score=sum(m.quality_score for m in missions) / total,
            common_patterns=common_workflows,
            timeframe_start=min(m.started_at for m in missions),
            timeframe_end=max(m.completed_at for m in missions),
        )

        return CrossMissionAggregation(
            aggregation_id=str(uuid4()),
            aggregation_type="by_domain",
            groupings=[grouping],
            total_missions_analyzed=total,
            overall_success_rate=success_rate,
            strategic_signals=[],
        )

    async def aggregate_by_timeframe(
        self,
        start: datetime,
        end: datetime,
    ) -> CrossMissionAggregation:
        """
        Aggregate missions by timeframe.

        Args:
            start: Start of timeframe
            end: End of timeframe

        Returns:
            CrossMissionAggregation with results
        """
        # Filter missions by timeframe
        missions = [
            m for m in self._mission_summaries.values()
            if m.started_at >= start and m.completed_at <= end
        ]

        if not missions:
            return CrossMissionAggregation(
                aggregation_type="by_timeframe",
                groupings=[],
                total_missions_analyzed=0,
                overall_success_rate=0.0,
            )

        # Group by mission type within timeframe
        type_groups = defaultdict(list)
        for m in missions:
            type_groups[m.mission_type].append(m)

        groupings = []
        for mtype, ms in type_groups.items():
            total = len(ms)
            successful = sum(1 for m in ms if m.success)
            success_rate = successful / total if total > 0 else 0.0

            groupings.append(MissionGrouping(
                grouping_id=f"timeframe_{mtype}",
                grouping_type="timeframe_mission_type",
                grouping_key=mtype,
                mission_ids=[m.mission_id for m in ms],
                total_missions=total,
                success_count=successful,
                success_rate=success_rate,
                avg_duration=sum(m.duration_seconds for m in ms) / total,
                avg_quality_score=sum(m.quality_score for m in ms) / total,
                timeframe_start=min(m.started_at for m in ms),
                timeframe_end=max(m.completed_at for m in ms),
            ))

        total = len(missions)
        successful = sum(1 for m in missions if m.success)
        overall_success_rate = successful / total if total > 0 else 0.0

        return CrossMissionAggregation(
            aggregation_id=str(uuid4()),
            aggregation_type="by_timeframe",
            groupings=groupings,
            total_missions_analyzed=total,
            overall_success_rate=overall_success_rate,
            strategic_signals=[],
        )

    async def get_all_aggregations(
        self,
        force_refresh: bool = False,
    ) -> List[CrossMissionAggregation]:
        """
        Get all available aggregations.

        Args:
            force_refresh: Force refresh of cached data

        Returns:
            List of aggregations
        """
        now = datetime.now()

        # Check cache
        if (
            not force_refresh
            and self._cache_time
            and (now - self._cache_time) < self._cache_ttl
        ):
            return list(self._cached_aggregations.values())

        # Generate aggregations
        aggregations = []

        # Aggregate by mission types
        mission_types = set(m.mission_type for m in self._mission_summaries.values())
        for mtype in mission_types:
            agg = await self.aggregate_by_mission_type(mtype)
            aggregations.append(agg)

        # Aggregate by domains
        domains = set(m.domain for m in self._mission_summaries.values() if m.domain)
        for domain in domains:
            agg = await self.aggregate_by_domain(domain)
            aggregations.append(agg)

        # Cache
        self._cached_aggregations = {
            agg.aggregation_id: agg
            for agg in aggregations
        }
        self._cache_time = now

        return aggregations

    async def get_mission_statistics(self) -> Dict[str, Any]:
        """
        Get statistics across all missions.

        Returns:
            Statistics dictionary
        """
        missions = list(self._mission_summaries.values())

        if not missions:
            return {
                "total_missions": 0,
                "success_rate": 0.0,
                "by_mission_type": {},
                "by_domain": {},
            }

        total = len(missions)
        successful = sum(1 for m in missions if m.success)
        success_rate = successful / total

        # By mission type
        by_type = defaultdict(list)
        for m in missions:
            by_type[m.mission_type].append(m)

        type_stats = {}
        for mtype, ms in by_type.items():
            type_successful = sum(1 for m in ms if m.success)
            type_stats[mtype] = {
                "count": len(ms),
                "success_rate": type_successful / len(ms) if ms else 0.0,
            }

        # By domain
        by_domain = defaultdict(list)
        for m in missions:
            if m.domain:
                by_domain[m.domain].append(m)

        domain_stats = {}
        for domain, ms in by_domain.items():
            domain_successful = sum(1 for m in ms if m.success)
            domain_stats[domain] = {
                "count": len(ms),
                "success_rate": domain_successful / len(ms) if ms else 0.0,
            }

        return {
            "total_missions": total,
            "successful_missions": successful,
            "success_rate": success_rate,
            "by_mission_type": type_stats,
            "by_domain": domain_stats,
        }


# Global cross-mission aggregator instance
_aggregator: Optional[CrossMissionAggregator] = None


def get_cross_mission_aggregator() -> CrossMissionAggregator:
    """Get the global cross-mission aggregator instance."""
    global _aggregator
    if _aggregator is None:
        _aggregator = CrossMissionAggregator()
    return _aggregator
