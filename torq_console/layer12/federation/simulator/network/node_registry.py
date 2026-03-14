"""
Node Registry for Federation Network Simulator

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Tracks simulated nodes and their evolving properties across long simulations.
Nodes behave differently across long horizons - this registry manages that evolution.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from pydantic import BaseModel, Field

from ..models import NodeType, NodeBehaviorProfile, Stance, Domain


logger = logging.getLogger(__name__)


# ============================================================================
# Node Network State
# ============================================================================

class NetworkNeighbor(BaseModel):
    """Represents a neighboring node in the federation network."""

    node_id: str = Field(..., description="Neighbor node ID")
    connection_strength: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Strength of connection to this neighbor"
    )
    trust_toward: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Trust score toward this neighbor"
    )
    last_interaction: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last interaction timestamp"
    )


class DomainInfluence(BaseModel):
    """Tracks a node's influence within a specific domain."""

    domain: Domain = Field(..., description="Domain of influence")
    influence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Influence score within this domain"
    )
    claims_published: int = Field(default=0, ge=0, description="Claims published in this domain")
    claims_accepted: int = Field(default=0, ge=0, description="Claims accepted in this domain")
    leadership_rank: Optional[int] = Field(
        None,
        ge=1,
        description="Rank in domain leadership (1=highest)"
    )


class NodeBehaviorMetrics(BaseModel):
    """Historical behavior metrics for a node."""

    total_claims_published: int = Field(default=0, ge=0)
    total_claims_accepted: int = Field(default=0, ge=0)
    total_claims_rejected: int = Field(default=0, ge=0)
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    trust_volatility: float = Field(
        default=0.0,
        ge=0.0,
        description="Standard deviation of trust changes"
    )
    trust_drift_rate: float = Field(
        default=0.0,
        description="Rate of trust change per epoch"
    )

    adversarial_flags: int = Field(
        default=0,
        ge=0,
        description="Count of adversarial behavior detections"
    )
    quarantine_count: int = Field(
        default=0,
        ge=0,
        description="Count of times node was quarantined"
    )


# ============================================================================
# Simulated Network Node
# ============================================================================

class SimulatedNetworkNode(BaseModel):
    """
    A node in the simulated federation network.

    Extends the basic SimulatedNode with network-aware properties:
    - Network neighbors and connections
    - Domain influence tracking
    - Historical behavior metrics
    - Long-horizon state evolution
    """

    # Core identity
    node_id: str = Field(..., description="Unique node identifier")
    node_type: NodeType = Field(default=NodeType.NORMAL, description="Node type classification")
    baseline_trust: float = Field(default=0.5, ge=0.0, le=1.0, description="Initial trust score")

    # Network position
    network_neighbors: Dict[str, NetworkNeighbor] = Field(
        default_factory=dict,
        description="Connected nodes in the network"
    )
    network_centrality: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Network centrality score"
    )

    # Domain specializations
    domain_specializations: List[Domain] = Field(
        default_factory=list,
        description="Domains this node specializes in"
    )
    domain_influence: Dict[str, DomainInfluence] = Field(
        default_factory=dict,
        description="Influence scores per domain"
    )

    # Behavioral profile
    behavior_profile: NodeBehaviorProfile = Field(
        default_factory=NodeBehaviorProfile,
        description="Behavioral characteristics"
    )
    stance_bias: Stance = Field(
        default=Stance.NEUTRAL,
        description="Default stance bias"
    )

    # Activity metrics
    claim_rate: float = Field(
        default=1.0,
        ge=0.0,
        description="Claims published per epoch (expected)"
    )
    quality_profile: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Average claim quality"
    )

    # Historical metrics
    behavior_metrics: NodeBehaviorMetrics = Field(
        default_factory=NodeBehaviorMetrics,
        description="Historical behavior tracking"
    )

    # State tracking
    current_trust: float = Field(default=0.5, ge=0.0, le=1.0, description="Current trust score")
    is_active: bool = Field(default=True, description="Whether node is active")
    is_quarantined: bool = Field(default=False, description="Whether node is quarantined")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Node Registry
# ============================================================================

class NodeRegistry:
    """
    Registry for simulated network nodes.

    Responsibilities:
    - Register and track nodes
    - Update node trust states
    - Track node influence over time
    - Monitor domain leadership
    - Detect behavior drift
    """

    def __init__(self):
        self._nodes: Dict[str, SimulatedNetworkNode] = {}
        self._domain_leaders: Dict[str, List[str]] = defaultdict(list)  # domain -> [node_ids]
        self.logger = logging.getLogger(__name__)

    def register_node(
        self,
        node_id: str,
        node_type: NodeType = NodeType.NORMAL,
        baseline_trust: float = 0.5,
        domain_specializations: Optional[List[Domain]] = None,
        behavior_profile: Optional[NodeBehaviorProfile] = None,
    ) -> SimulatedNetworkNode:
        """
        Register a new node in the network.

        Args:
            node_id: Unique node identifier
            node_type: Type of node
            baseline_trust: Initial trust score
            domain_specializations: Domains this node specializes in
            behavior_profile: Behavioral characteristics

        Returns:
            The registered SimulatedNetworkNode
        """
        node = SimulatedNetworkNode(
            node_id=node_id,
            node_type=node_type,
            baseline_trust=baseline_trust,
            current_trust=baseline_trust,
            domain_specializations=domain_specializations or [],
            behavior_profile=behavior_profile or NodeBehaviorProfile(),
        )

        self._nodes[node_id] = node
        self.logger.info(f"Registered node {node_id} (type={node_type}, trust={baseline_trust:.2f})")

        return node

    def get_node(self, node_id: str) -> Optional[SimulatedNetworkNode]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[SimulatedNetworkNode]:
        """Get all registered nodes."""
        return list(self._nodes.values())

    def update_trust_state(self, node_id: str, new_trust: float) -> None:
        """
        Update a node's trust score and track metrics.

        Args:
            node_id: Node to update
            new_trust: New trust score
        """
        node = self._nodes.get(node_id)
        if not node:
            self.logger.warning(f"Cannot update trust for unknown node {node_id}")
            return

        old_trust = node.current_trust
        node.current_trust = new_trust
        node.last_updated = datetime.utcnow()

        # Update behavior metrics
        node.behavior_metrics.total_claims_published += 1
        if new_trust > old_trust:
            node.behavior_metrics.total_claims_accepted += 1

        # Recalculate acceptance rate
        total = node.behavior_metrics.total_claims_published
        if total > 0:
            node.behavior_metrics.acceptance_rate = (
                node.behavior_metrics.total_claims_accepted / total
            )

        self.logger.debug(f"Updated trust for {node_id}: {old_trust:.2f} -> {new_trust:.2f}")

    def add_network_neighbor(
        self,
        node_id: str,
        neighbor_id: str,
        connection_strength: float = 1.0,
    ) -> None:
        """
        Add a network connection between two nodes.

        Args:
            node_id: Source node
            neighbor_id: Target neighbor
            connection_strength: Strength of connection (0-1)
        """
        node = self._nodes.get(node_id)
        if not node:
            self.logger.warning(f"Cannot add neighbor to unknown node {node_id}")
            return

        neighbor = NetworkNeighbor(
            node_id=neighbor_id,
            connection_strength=connection_strength,
            trust_toward=0.5,  # Initial trust
        )

        node.network_neighbors[neighbor_id] = neighbor
        self.logger.debug(f"Added neighbor {neighbor_id} to {node_id}")

    def update_domain_influence(
        self,
        node_id: str,
        domain: Domain,
        claim_accepted: bool,
    ) -> None:
        """
        Update a node's influence in a domain.

        Args:
            node_id: Node to update
            domain: Domain of the claim
            claim_accepted: Whether the claim was accepted
        """
        node = self._nodes.get(node_id)
        if not node:
            return

        domain_key = domain.value
        if domain_key not in node.domain_influence:
            node.domain_influence[domain_key] = DomainInfluence(domain=domain)

        influence = node.domain_influence[domain_key]
        influence.claims_published += 1
        if claim_accepted:
            influence.claims_accepted += 1

        # Recalculate influence score
        if influence.claims_published > 0:
            influence.influence_score = (
                influence.claims_accepted / influence.claims_published
            )

        # Update domain leadership tracking
        self._update_domain_leadership(domain)

    def _update_domain_leadership(self, domain: Domain) -> None:
        """Recalculate domain leadership rankings."""
        domain_key = domain.value

        # Get all nodes with influence in this domain
        node_influence = []
        for node in self._nodes.values():
            if domain_key in node.domain_influence:
                influence = node.domain_influence[domain_key]
                node_influence.append((node.node_id, influence.influence_score))

        # Sort by influence score (descending)
        node_influence.sort(key=lambda x: x[1], reverse=True)

        # Update rankings
        self._domain_leaders[domain_key] = [node_id for node_id, _ in node_influence]

        # Assign leadership ranks
        for rank, (node_id, _) in enumerate(node_influence, start=1):
            node = self._nodes.get(node_id)
            if node and domain_key in node.domain_influence:
                node.domain_influence[domain_key].leadership_rank = rank

    def get_domain_leaders(self, domain: Domain, top_n: int = 5) -> List[str]:
        """
        Get top leaders in a domain.

        Args:
            domain: Domain to query
            top_n: Number of top leaders to return

        Returns:
            List of node IDs ordered by influence
        """
        domain_key = domain.value
        leaders = self._domain_leaders.get(domain_key, [])
        return leaders[:top_n]

    def track_node_influence(self, node_id: str) -> Dict[str, float]:
        """
        Get a node's influence across all domains.

        Args:
            node_id: Node to query

        Returns:
            Dict mapping domain -> influence_score
        """
        node = self._nodes.get(node_id)
        if not node:
            return {}

        return {
            domain: influence.influence_score
            for domain, influence in node.domain_influence.items()
        }

    def monitor_behavior_drift(self, node_id: str) -> Dict[str, Any]:
        """
        Check if a node's behavior is drifting significantly.

        Args:
            node_id: Node to monitor

        Returns:
            Dict with drift indicators
        """
        node = self._nodes.get(node_id)
        if not node:
            return {}

        metrics = node.behavior_metrics

        # Calculate trust drift
        trust_drift = abs(node.current_trust - node.baseline_trust)
        significant_drift = trust_drift > 0.3

        # Check acceptance rate decline
        acceptance_decline = metrics.acceptance_rate < 0.3 and metrics.total_claims_published > 10

        # Check adversarial pattern
        adversarial_pattern = metrics.adversarial_flags > 3

        is_drifting = significant_drift or acceptance_decline or adversarial_pattern

        return {
            "node_id": node_id,
            "is_drifting": is_drifting,
            "trust_drift": trust_drift,
            "acceptance_rate": metrics.acceptance_rate,
            "adversarial_flags": metrics.adversarial_flags,
            "quarantine_count": metrics.quarantine_count,
        }

    def get_network_statistics(self) -> Dict[str, Any]:
        """Get overall network statistics."""
        if not self._nodes:
            return {
                "total_nodes": 0,
                "active_nodes": 0,
                "quarantined_nodes": 0,
            }

        return {
            "total_nodes": len(self._nodes),
            "active_nodes": sum(1 for n in self._nodes.values() if n.is_active),
            "quarantined_nodes": sum(1 for n in self._nodes.values() if n.is_quarantined),
            "avg_trust": sum(n.current_trust for n in self._nodes.values()) / len(self._nodes),
            "total_connections": sum(len(n.network_neighbors) for n in self._nodes.values()),
        }


def create_node_registry() -> NodeRegistry:
    """Factory function to create a NodeRegistry."""
    return NodeRegistry()
