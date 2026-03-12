"""
TORQ Control Plane - Intelligence Aggregator

L7-M1: Aggregates intelligence from all TORQ layers.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import models
from .models import (
    LayerType,
    LayerStatus,
    IntelligenceLayer,
    IntelligenceView,
    InsightStatus,
    InsightView,
    MemoryItem,
    MemoryStatistics,
    create_layer_status,
    get_default_layers,
)


# ============================================================================
# Intelligence Aggregator
# ============================================================================

class IntelligenceAggregator:
    """
    Aggregates intelligence from all TORQ layers.

    Collects metrics and status from:
    - Execution Layer
    - Artifacts Layer
    - Governed Memory
    - Insight Intelligence
    - Pattern Intelligence
    - Readiness Governance
    - Governance Actions
    """

    def __init__(self):
        """Initialize the intelligence aggregator."""
        self._layers: Dict[LayerType, IntelligenceLayer] = {}
        self._initialize_layers()

        # Cache
        self._cached_view: Optional[IntelligenceView] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=30)

    def _initialize_layers(self):
        """Initialize default layer configurations."""
        for layer in get_default_layers():
            self._layers[layer.layer_type] = layer

    async def get_intelligence_view(self, force_refresh: bool = False) -> IntelligenceView:
        """
        Get aggregated intelligence view.

        Args:
            force_refresh: Force refresh of cached data

        Returns:
            IntelligenceView with current system state
        """
        now = datetime.now()

        # Return cached if fresh
        if (
            not force_refresh
            and self._cached_view
            and self._cache_time
            and (now - self._cache_time) < self._cache_ttl
        ):
            return self._cached_view

        # Refresh all layers
        await self._refresh_all_layers()

        # Build view
        view = IntelligenceView(
            layers=list(self._layers.values()),
            total_items=sum(l.item_count for l in self._layers.values()),
            active_processes=sum(
                l.metrics.get("active_processes", 0) for l in self._layers.values()
            ),
            system_health=sum(l.health_score for l in self._layers.values()) / len(self._layers),
            recent_insights=await self._get_recent_insights(limit=5),
            recent_patterns=await self._get_recent_patterns(limit=5),
            recent_governance_actions=await self._get_recent_governance_actions(limit=5),
            active_alerts=await self._get_active_alerts(),
        )

        # Cache
        self._cached_view = view
        self._cache_time = now

        return view

    async def _refresh_all_layers(self):
        """Refresh metrics for all layers."""
        tasks = [
            self._refresh_execution_layer(),
            self._refresh_artifacts_layer(),
            self._refresh_memory_layer(),
            self._refresh_insights_layer(),
            self._refresh_patterns_layer(),
            self._refresh_readiness_layer(),
            self._refresh_governance_layer(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error refreshing layer: {result}")

    async def _refresh_execution_layer(self):
        """Refresh execution layer metrics."""
        try:
            # Placeholder - would integrate with execution tracking
            layer = self._layers.get(LayerType.EXECUTION)
            if layer:
                layer.metrics = {
                    "active_processes": 0,
                    "completed_today": 0,
                    "error_rate": 0.0,
                }
                layer.last_activity = datetime.now()
        except Exception as e:
            logger.warning(f"Error refreshing execution layer: {e}")

    async def _refresh_artifacts_layer(self):
        """Refresh artifacts layer metrics."""
        try:
            # Placeholder - would integrate with artifacts tracking
            layer = self._layers.get(LayerType.ARTIFACTS)
            if layer:
                layer.metrics = {
                    "total_artifacts": 0,
                    "validated_artifacts": 0,
                    "storage_used_mb": 0,
                }
                layer.last_activity = datetime.now()
        except Exception as e:
            logger.warning(f"Error refreshing artifacts layer: {e}")

    async def _refresh_memory_layer(self):
        """Refresh governed memory metrics."""
        try:
            # Placeholder - would integrate with governed memory
            layer = self._layers.get(LayerType.MEMORY)
            if layer:
                stats = await self.get_memory_statistics()
                layer.item_count = stats.total_items
                layer.metrics = {
                    "governed_items": stats.governed_items,
                    "validated_items": stats.validated_items,
                    "avg_confidence": stats.avg_confidence,
                }
                layer.last_activity = datetime.now()
        except Exception as e:
            logger.warning(f"Error refreshing memory layer: {e}")

    async def _refresh_insights_layer(self):
        """Refresh insight intelligence metrics."""
        try:
            from ...insights.publishing import get_insight_service
            service = get_insight_service()

            layer = self._layers.get(LayerType.INSIGHTS)
            if layer:
                # Get metrics from insight service
                layer.item_count = 0  # service.get_total_insights()
                layer.metrics = {
                    "pending_insights": 0,
                    "approved_insights": 0,
                    "published_insights": 0,
                }
                layer.last_activity = datetime.now()
        except ImportError:
            logger.debug("Insight service not available")
        except Exception as e:
            logger.warning(f"Error refreshing insights layer: {e}")

    async def _refresh_patterns_layer(self):
        """Refresh pattern intelligence metrics."""
        try:
            # Placeholder - would integrate with pattern tracking
            layer = self._layers.get(LayerType.PATTERNS)
            if layer:
                layer.item_count = 0
                layer.metrics = {
                    "discovered_patterns": 0,
                    "validated_patterns": 0,
                    "active_in_production": 0,
                }
                layer.last_activity = datetime.now()
        except Exception as e:
            logger.warning(f"Error refreshing patterns layer: {e}")

    async def _refresh_readiness_layer(self):
        """Refresh readiness governance metrics."""
        try:
            from ...readiness.query_service import get_query_service
            from ...readiness.analytics_service import get_analytics_service

            query_service = get_query_service()
            analytics_service = get_analytics_service()

            layer = self._layers.get(LayerType.READINESS)
            if layer:
                candidates = query_service.list_candidates()
                metrics = analytics_service.get_metrics()

                layer.item_count = candidates.total_count
                layer.metrics = {
                    "ready_candidates": metrics.ready_candidates,
                    "blocked_candidates": metrics.blocked_count,
                    "watchlist_candidates": (
                        metrics.state_distribution.get("watchlist", {}).get("count", 0)
                        if isinstance(metrics.state_distribution, dict)
                        else sum(s.count for s in metrics.state_distribution if s.state == "watchlist")
                    ),
                    "promotion_rate": metrics.promotion_rate,
                }
                layer.last_activity = datetime.now()
        except ImportError:
            logger.debug("Readiness service not available")
        except Exception as e:
            logger.warning(f"Error refreshing readiness layer: {e}")

    async def _refresh_governance_layer(self):
        """Refresh governance actions metrics."""
        try:
            from ...governance.controller import get_governance_controller

            controller = get_governance_controller()
            view = controller.get_governance_view()

            layer = self._layers.get(LayerType.GOVERNANCE)
            if layer:
                layer.item_count = view.pending_actions
                layer.metrics = {
                    "pending_actions": view.pending_actions,
                    "ready_candidates": view.ready_candidates,
                    "blocked_candidates": view.blocked_candidates,
                }
                layer.last_activity = datetime.now()
        except ImportError:
            logger.debug("Governance controller not available")
        except Exception as e:
            logger.warning(f"Error refreshing governance layer: {e}")

    # ------------------------------------------------------------------------
    # Data Retrieval
    # ------------------------------------------------------------------------

    async def _get_recent_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent insights."""
        try:
            # Placeholder - would integrate with insight system
            return []
        except Exception as e:
            logger.warning(f"Error getting recent insights: {e}")
            return []

    async def _get_recent_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent patterns."""
        try:
            # Placeholder - would integrate with pattern system
            return []
        except Exception as e:
            logger.warning(f"Error getting recent patterns: {e}")
            return []

    async def _get_recent_governance_actions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent governance actions."""
        try:
            from ...governance.controller import get_governance_controller
            controller = get_governance_controller()
            overrides = controller.get_overrides(limit=limit)

            return [
                {
                    "id": str(o.id),
                    "type": "override",
                    "target": o.target_id,
                    "decision": o.override_decision,
                    "by": o.overridden_by,
                    "at": o.overridden_at.isoformat(),
                }
                for o in overrides
            ]
        except ImportError:
            logger.debug("Governance controller not available")
            return []
        except Exception as e:
            logger.warning(f"Error getting governance actions: {e}")
            return []

    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts."""
        try:
            # Return empty list for now - state manager alerts not needed
            return []
        except Exception as e:
            logger.warning(f"Error getting active alerts: {e}")
            return []

    # ------------------------------------------------------------------------
    # Memory Statistics
    # ------------------------------------------------------------------------

    async def get_memory_statistics(self) -> MemoryStatistics:
        """
        Get governed memory statistics.

        Returns:
            MemoryStatistics with current memory state
        """
        # Placeholder - would integrate with governed memory
        return MemoryStatistics()

    async def get_memory_items(
        self,
        limit: int = 100,
        item_type: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        Get governed memory items.

        Args:
            limit: Maximum number of items
            item_type: Optional type filter

        Returns:
            List of MemoryItem
        """
        # Placeholder - would integrate with governed memory
        return []

    async def search_memory(
        self,
        query: str,
        limit: int = 50,
    ) -> List[MemoryItem]:
        """
        Search governed memory.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching MemoryItem
        """
        # Placeholder - would integrate with governed memory search
        return []


# Global intelligence aggregator instance
_aggregator: Optional[IntelligenceAggregator] = None


def get_intelligence_aggregator() -> IntelligenceAggregator:
    """Get the global intelligence aggregator instance."""
    global _aggregator
    if _aggregator is None:
        _aggregator = IntelligenceAggregator()
    return _aggregator
