"""
TORQ Layer 11 - Capability Router

L11-M1: Routes workloads to the best available TORQ node.

The CapabilityRouter provides:
- Intelligent workload routing based on capabilities
- Latency and cost optimization
- Governance constraint enforcement
- Automatic failover support

All routing decisions respect Pre-Fabric Boundary Hardening (PRD-011-PRE).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from pydantic import BaseModel, Field

from .models import (
    NodeInfo,
    NodeStatus,
    NodeTier,
    NodeRegion,
    NodeType,
    NodeCapability,
    RoutingRequest,
    RoutingDecision,
    RoutingCapability,
    RoutingConstraints,
)
from .node_registry_service import get_node_registry_service


logger = logging.getLogger(__name__)


# ============================================================================
# Routing Strategy
# ============================================================================

class RoutingStrategy(str, Enum):
    """Strategies for routing workloads."""
    LOWEST_LATENCY = "lowest_latency"      # Minimize response time
    BALANCED = "balanced"                  # Balance latency and cost
    COST_OPTIMIZED = "cost_optimized"      # Minimize cost
    REGION_LOCAL = "region_local"          # Stay in same region
    HIGH_AVAILABILITY = "high_availability"  # Prefer most reliable nodes


class RoutingScore(BaseModel):
    """Score for a routing candidate."""
    node_id: UUID
    node_name: str

    # Scoring
    overall_score: float = Field(ge=0.0, le=1.0)
    latency_score: float = Field(ge=0.0, le=1.0)
    capacity_score: float = Field(ge=0.0, le=1.0)
    health_score: float = Field(ge=0.0, le=1.0)
    cost_score: float = Field(ge=0.0, le=1.0)

    # Details
    estimated_latency_ms: float
    available_capacity: int
    match_details: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Capability Router
# ============================================================================

class CapabilityRouter:
    """
    Routes workloads to the best available TORQ node.

    The router considers:
    - Capability availability and matching
    - Current health and capacity
    - Latency and cost optimization
    - Governance constraints
    - Geographic and tier preferences
    """

    def __init__(self):
        """Initialize the capability router."""
        self._registry = get_node_registry_service()

        # Routing history
        self._routing_history: Dict[UUID, List[RoutingDecision]] = defaultdict(list)

        # Statistics
        self._total_routes: int = 0
        self._routes_by_node: Dict[UUID, int] = defaultdict(int)
        self._routes_by_strategy: Dict[str, int] = defaultdict(int)

    async def route_workload(
        self,
        request: RoutingRequest,
    ) -> RoutingDecision:
        """
        Route a workload to the best available node.

        Args:
            request: Routing request with capability requirements

        Returns:
            RoutingDecision with selected node
        """
        # Determine routing strategy
        strategy = self._determine_strategy(request)

        # Get candidate nodes
        candidates = await self._get_candidate_nodes(request)

        if not candidates:
            # No suitable nodes available
            return RoutingDecision(
                request_id=request.request_id,
                selected_node_id=uuid4(),  # Placeholder
                selected_node_name="NO_SUITABLE_NODE",
                confidence=0.0,
                routing_score=0.0,
                routing_reason="No nodes meet the required criteria",
                estimated_latency_ms=float('inf'),
            )

        # Score candidates
        scored = await self._score_candidates(candidates, request, strategy)

        # Select best candidate
        selected = scored[0]

        # Build fallback list
        fallback_nodes = [s.node_id for s in scored[1:4]]  # Top 3 fallbacks

        # Create decision
        decision = RoutingDecision(
            request_id=request.request_id,
            selected_node_id=selected.node_id,
            selected_node_name=selected.node_name,
            confidence=selected.overall_score,
            routing_score=selected.overall_score,
            routing_reason=self._format_routing_reason(selected, strategy),
            considered_alternatives=[
                {
                    "node_id": str(s.node_id),
                    "node_name": s.node_name,
                    "score": s.overall_score,
                }
                for s in scored[1:5]
            ],
            fallback_nodes=fallback_nodes,
            estimated_latency_ms=selected.estimated_latency_ms,
        )

        # Record routing
        self._record_routing(decision, strategy)

        logger.info(
            f"[CapabilityRouter] Routed workload {request.request_id} "
            f"to {selected.node_name} (score: {selected.overall_score:.2f})"
        )

        return decision

    def _determine_strategy(self, request: RoutingRequest) -> RoutingStrategy:
        """Determine routing strategy from request constraints."""
        constraints = request.constraints

        # Explicit cost preference
        if constraints.cost_preference == "low_latency":
            return RoutingStrategy.LOWEST_LATENCY
        elif constraints.cost_preference == "cost_optimized":
            return RoutingStrategy.COST_OPTIMIZED

        # Region preference
        if constraints.preferred_regions:
            return RoutingStrategy.REGION_LOCAL

        # High priority prefers availability
        if request.priority >= 8:
            return RoutingStrategy.HIGH_AVAILABILITY

        # Default to balanced
        return RoutingStrategy.BALANCED

    async def _get_candidate_nodes(
        self,
        request: RoutingRequest,
    ) -> List[NodeInfo]:
        """Get candidate nodes that meet the routing criteria."""
        constraints = request.constraints

        # Start with all healthy nodes
        candidates = self._registry.get_healthy_nodes()

        # Filter by excluded nodes
        if constraints.excluded_nodes:
            candidates = [n for n in candidates if n.node_id not in constraints.excluded_nodes]

        # Filter by tier requirement
        if constraints.required_tier:
            candidates = [n for n in candidates if n.identity.node_tier == constraints.required_tier]

        # Filter by preferred regions (if specified)
        if constraints.preferred_regions:
            region_candidates = [n for n in candidates if n.identity.region in constraints.preferred_regions]
            if region_candidates:
                candidates = region_candidates

        # Filter by capability requirements
        candidates = [
            n for n in candidates
            if self._meets_capability_requirements(n, request.capability_requirements)
        ]

        # Filter by capacity
        candidates = [n for n in candidates if n.can_accept_workload]

        # Filter by governance tags
        if constraints.governance_tags:
            candidates = [
                n for n in candidates
                if any(tag in n.identity.tags for tag in constraints.governance_tags)
            ]

        return candidates

    def _meets_capability_requirements(
        self,
        node: NodeInfo,
        requirements: List[RoutingCapability],
    ) -> bool:
        """Check if a node meets all capability requirements."""
        node_caps = {c.capability_name: c for c in node.capabilities}

        for req in requirements:
            cap = node_caps.get(req.capability_name)
            if not cap:
                return False

            # Check capacity
            if cap.current_workload_count + req.min_capacity > cap.max_concurrent_workloads:
                return False

            # Check required features
            for feature in req.required_features:
                if feature not in cap.supported_features:
                    return False

            # Check domain support
            if req.preferred_domains:
                if not any(d in cap.enabled_domains for d in req.preferred_domains):
                    return False

        return True

    async def _score_candidates(
        self,
        candidates: List[NodeInfo],
        request: RoutingRequest,
        strategy: RoutingStrategy,
    ) -> List[RoutingScore]:
        """Score candidates based on routing criteria."""
        scored = []

        for node in candidates:
            score = await self._score_node(node, request, strategy)
            scored.append(score)

        # Sort by overall score
        scored.sort(key=lambda s: s.overall_score, reverse=True)

        return scored

    async def _score_node(
        self,
        node: NodeInfo,
        request: RoutingRequest,
        strategy: RoutingStrategy,
    ) -> RoutingScore:
        """Score a single node for routing."""
        # Health score
        health_score = node.health.health_score

        # Capacity score
        available_capacity = sum(
            cap.max_concurrent_workloads - cap.current_workload_count
            for cap in node.capabilities
        )
        capacity_score = min(1.0, available_capacity / 10.0)  # Normalize

        # Latency score
        avg_latency = node.health.avg_response_time_ms
        if request.constraints.max_latency_ms:
            latency_score = max(0.0, 1.0 - (avg_latency / request.constraints.max_latency_ms))
        else:
            latency_score = max(0.0, 1.0 - (avg_latency / 1000.0))  # 1s baseline

        # Cost score (simplified)
        cost_score = self._calculate_cost_score(node, request, strategy)

        # Combine based on strategy
        overall_score = self._combine_scores(
            health_score=health_score,
            capacity_score=capacity_score,
            latency_score=latency_score,
            cost_score=cost_score,
            strategy=strategy,
        )

        return RoutingScore(
            node_id=node.node_id,
            node_name=node.identity.node_name,
            overall_score=overall_score,
            latency_score=latency_score,
            capacity_score=capacity_score,
            health_score=health_score,
            cost_score=cost_score,
            estimated_latency_ms=avg_latency,
            available_capacity=available_capacity,
            match_details={
                "strategy": strategy.value,
                "region": node.identity.region.value,
                "tier": node.identity.node_tier.value,
            },
        )

    def _calculate_cost_score(
        self,
        node: NodeInfo,
        request: RoutingRequest,
        strategy: RoutingStrategy,
    ) -> float:
        """Calculate cost score for a node."""
        # Simplified cost model based on tier
        tier_costs = {
            NodeTier.ENTERPRISE: 1.0,
            NodeTier.STANDARD: 0.7,
            NodeTier.EDGE: 0.5,
            NodeTier.RESEARCH: 0.3,
        }

        base_cost = tier_costs.get(node.identity.node_tier, 0.5)

        if strategy == RoutingStrategy.COST_OPTIMIZED:
            # Lower cost is better
            return 1.0 - base_cost
        elif strategy == RoutingStrategy.LOWEST_LATENCY:
            # Cost matters less
            return 0.5
        else:
            # Balanced
            return 1.0 - (base_cost * 0.5)

    def _combine_scores(
        self,
        health_score: float,
        capacity_score: float,
        latency_score: float,
        cost_score: float,
        strategy: RoutingStrategy,
    ) -> float:
        """Combine component scores into overall score."""
        weights = {
            RoutingStrategy.LOWEST_LATENCY: {
                "health": 0.2,
                "capacity": 0.1,
                "latency": 0.6,
                "cost": 0.1,
            },
            RoutingStrategy.BALANCED: {
                "health": 0.3,
                "capacity": 0.2,
                "latency": 0.3,
                "cost": 0.2,
            },
            RoutingStrategy.COST_OPTIMIZED: {
                "health": 0.2,
                "capacity": 0.2,
                "latency": 0.1,
                "cost": 0.5,
            },
            RoutingStrategy.REGION_LOCAL: {
                "health": 0.3,
                "capacity": 0.2,
                "latency": 0.4,
                "cost": 0.1,
            },
            RoutingStrategy.HIGH_AVAILABILITY: {
                "health": 0.6,
                "capacity": 0.2,
                "latency": 0.1,
                "cost": 0.1,
            },
        }

        w = weights.get(strategy, weights[RoutingStrategy.BALANCED])

        return (
            w["health"] * health_score +
            w["capacity"] * capacity_score +
            w["latency"] * latency_score +
            w["cost"] * cost_score
        )

    def _format_routing_reason(self, score: RoutingScore, strategy: RoutingStrategy) -> str:
        """Format human-readable routing reason."""
        return (
            f"Selected {score.node_name} using {strategy.value} strategy "
            f"(overall score: {score.overall_score:.2f}, "
            f"latency: {score.estimated_latency_ms:.0f}ms, "
            f"capacity: {score.available_capacity})"
        )

    def _record_routing(self, decision: RoutingDecision, strategy: RoutingStrategy) -> None:
        """Record routing decision for analytics."""
        self._total_routes += 1
        self._routes_by_node[decision.selected_node_id] += 1
        self._routes_by_strategy[strategy.value] += 1

        self._routing_history[decision.request_id].append(decision)

        # Keep history manageable
        if len(self._routing_history[decision.request_id]) > 100:
            self._routing_history[decision.request_id] = self._routing_history[decision.request_id][-100:]

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            "total_routes": self._total_routes,
            "routes_by_node": {
                str(node_id): count
                for node_id, count in self._routes_by_node.items()
            },
            "routes_by_strategy": dict(self._routes_by_strategy),
        }

    async def validate_routing(
        self,
        node_id: UUID,
        request: RoutingRequest,
    ) -> bool:
        """
        Validate if a node can handle a routing request.

        Args:
            node_id: Node to validate
            request: Routing request to validate against

        Returns:
            True if node can handle the request
        """
        node = self._registry.get_node(node_id)
        if not node:
            return False

        if not node.is_healthy:
            return False

        return self._meets_capability_requirements(node, request.capability_requirements)


# Global capability router instance
_router: Optional[CapabilityRouter] = None


def get_capability_router() -> CapabilityRouter:
    """Get the global capability router instance."""
    global _router
    if _router is None:
        _router = CapabilityRouter()
    return _router
