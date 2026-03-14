"""
Node Registry for Multi-Node Federation Simulation

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Central registry for managing node identity, trust state, domain specialization,
influence tracking, and behavior profiles in 10-50 node federation simulations.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from ..models import Domain, Stance


logger = logging.getLogger(__name__)


@dataclass
class NodeIdentity:
    """Unique node identity and credentials."""

    node_id: str
    display_name: str
    public_key: str
    key_id: str
    created_at: datetime
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, other):
        return isinstance(other, NodeIdentity) and self.node_id == other.node_id


@dataclass
class NodeTrustState:
    """Dynamic trust state for a node.

    Tracks current trust, rate of change (velocity), and quarantine status.
    """

    node_id: str
    baseline_trust: float = 0.5
    current_trust: float = 0.5
    trust_velocity: float = 0.0  # Rate of change per epoch
    quarantined: bool = False
    quarantine_reason: Optional[str] = None
    quarantine_since: Optional[datetime] = None
    adjustment_history: List[float] = field(default_factory=list)
    last_adjustment_at: Optional[datetime] = None

    def apply_adjustment(self, adjustment: float, timestamp: Optional[datetime] = None) -> None:
        """Apply a trust adjustment and update velocity."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        old_trust = self.current_trust
        self.current_trust = max(0.0, min(1.0, self.current_trust + adjustment))

        # Update velocity (exponential moving average)
        if self.adjustment_history:
            self.trust_velocity = 0.7 * self.trust_velocity + 0.3 * adjustment
        else:
            self.trust_velocity = adjustment

        self.adjustment_history.append(adjustment)
        self.last_adjustment_at = timestamp

        # Check quarantine thresholds
        if self.current_trust < 0.2 and not self.quarantined:
            self.quarantined = True
            self.quarantine_reason = "Trust below threshold"
            self.quarantine_since = timestamp
        elif self.current_trust >= 0.4 and self.quarantined:
            self.quarantined = False
            self.quarantine_reason = None
            self.quarantine_since = None

    def decay(self, decay_rate: float = 0.01) -> None:
        """Apply trust decay."""
        self.apply_adjustment(-decay_rate * self.current_trust)

    def get_trust_tier(self) -> str:
        """Get trust tier classification."""
        if self.quarantined:
            return "quarantined"
        if self.current_trust >= 0.8:
            return "trusted"
        if self.current_trust >= 0.6:
            return "verified"
        if self.current_trust >= 0.4:
            return "probationary"
        return "untrusted"


@dataclass
class DomainSpecialization:
    """Node's domain expertise and influence.

    Tracks which domains a node specializes in and their confidence level
    in each domain.
    """

    primary_domain: Domain
    secondary_domains: List[Domain] = field(default_factory=list)
    domain_confidence: Dict[Domain, float] = field(default_factory=dict)
    publication_count: Dict[Domain, int] = field(default_factory=dict)
    acceptance_rate: Dict[Domain, float] = field(default_factory=dict)

    def __post_init__(self):
        # Initialize confidence for primary domain
        if self.primary_domain not in self.domain_confidence:
            self.domain_confidence[self.primary_domain] = 0.8
        if self.primary_domain not in self.publication_count:
            self.publication_count[self.primary_domain] = 0
        if self.primary_domain not in self.acceptance_rate:
            self.acceptance_rate[self.primary_domain] = 0.7

    def record_publication(self, domain: Domain, accepted: bool) -> None:
        """Record a publication in a domain."""
        self.publication_count[domain] = self.publication_count.get(domain, 0) + 1

        # Update acceptance rate (exponential moving average)
        current_rate = self.acceptance_rate.get(domain, 0.5)
        new_rate = 0.8 * current_rate + 0.2 * (1.0 if accepted else 0.0)
        self.acceptance_rate[domain] = new_rate

    def get_confidence(self, domain: Domain) -> float:
        """Get confidence level for a domain."""
        return self.domain_confidence.get(domain, 0.3)

    def is_specialist(self, domain: Domain) -> bool:
        """Check if node is a specialist in the domain."""
        return domain == self.primary_domain or domain in self.secondary_domains

    def get_domains(self) -> List[Domain]:
        """Get all domains this node publishes in."""
        return [self.primary_domain] + self.secondary_domains


@dataclass
class InfluenceProfile:
    """Node's influence in the federation.

    Tracks both raw influence (derived from trust and acceptance) and
    network position (followers, citations).
    """

    node_id: str
    raw_influence: float = 0.0
    normalized_influence: float = 0.0
    domain_dominance: Dict[Domain, float] = field(default_factory=dict)
    follower_count: int = 0
    citation_count: int = 0
    last_updated: Optional[datetime] = None

    def update_influence(self, base_score: float, network_max: float = 1.0) -> None:
        """Update influence scores."""
        self.raw_influence = base_score
        self.normalized_influence = base_score / network_max if network_max > 0 else 0.0
        self.last_updated = datetime.utcnow()

    def record_citation(self) -> None:
        """Record a citation (another node referenced this node)."""
        self.citation_count += 1

    def add_follower(self) -> None:
        """Record a new follower."""
        self.follower_count += 1

    def remove_follower(self) -> None:
        """Remove a follower."""
        self.follower_count = max(0, self.follower_count - 1)

    def get_domain_dominance(self, domain: Domain) -> float:
        """Get dominance score in a specific domain."""
        return self.domain_dominance.get(domain, 0.0)

    def set_domain_dominance(self, domain: Domain, score: float) -> None:
        """Set dominance score for a domain."""
        self.domain_dominance[domain] = max(0.0, min(1.0, score))


@dataclass
class BehaviorProfile:
    """Node's behavioral tendencies and adversarial mode.

    Controls claim generation frequency, stance distribution, quality,
    and adversarial behavior patterns.
    """

    node_id: str
    claim_frequency: float = 1.0  # claims per epoch (multiplier)
    stance_distribution: Dict[Stance, float] = field(default_factory=dict)
    quality_mean: float = 0.7
    quality_std: float = 0.15
    adversarial_mode: Optional[str] = None  # None, "flood", "monoculture", "capture", "sybil"
    adversarial_intensity: float = 0.0  # 0.0 to 1.0
    coordination_group: Optional[str] = None  # For coordinated attacks
    last_behavior_change: Optional[datetime] = None

    def __post_init__(self):
        # Default stance distribution (uniform)
        if not self.stance_distribution:
            for stance in Stance:
                self.stance_distribution[stance] = 1.0 / len(Stance)

    def get_claim_count_for_epoch(self, base_claims: int = 1) -> int:
        """Get number of claims this node should generate in an epoch."""
        import random
        count = int(base_claims * self.claim_frequency)
        # Add some randomness
        if random.random() < (self.claim_frequency * base_claims - count):
            count += 1
        return max(0, count)

    def sample_stance(self) -> Stance:
        """Sample a stance based on distribution."""
        import random
        stances = list(self.stance_distribution.keys())
        weights = [self.stance_distribution[s] for s in stances]
        return random.choices(stances, weights=weights, k=1)[0]

    def sample_quality(self) -> float:
        """Sample a quality score."""
        import random
        quality = random.gauss(self.quality_mean, self.quality_std)
        return max(0.0, min(1.0, quality))

    def is_adversarial(self) -> bool:
        """Check if node is in adversarial mode."""
        return self.adversarial_mode is not None and self.adversarial_intensity > 0.0

    def set_adversarial_mode(self, mode: str, intensity: float = 0.5, group: Optional[str] = None) -> None:
        """Set adversarial behavior mode."""
        self.adversarial_mode = mode
        self.adversarial_intensity = max(0.0, min(1.0, intensity))
        self.coordination_group = group
        self.last_behavior_change = datetime.utcnow()

        # Adjust behavior based on mode
        if mode == "flood":
            self.claim_frequency = 1.0 + (intensity * 4.0)  # Up to 5x frequency
            self.quality_mean = 0.7 - (intensity * 0.3)  # Lower quality
        elif mode == "monoculture":
            # Concentrate stance distribution
            target_stance = Stance.SUPPORT
            for s in Stance:
                self.stance_distribution[s] = 1.0 if s == target_stance else 0.0
        elif mode == "capture":
            self.quality_mean = 0.8 + (intensity * 0.2)  # Higher quality to gain trust
            self.quality_std = 0.05  # More consistent
        elif mode == "sybil":
            self.claim_frequency = 0.5  # Lower frequency to avoid detection
            self.quality_mean = 0.6 + (intensity * 0.2)


@dataclass
class FederatedNode:
    """Complete node representation for Phase 2B simulation.

    Combines identity, trust state, domain specialization, influence,
    and behavior into a single node model.
    """

    identity: NodeIdentity
    trust_state: NodeTrustState
    domain_spec: DomainSpecialization
    influence: InfluenceProfile
    behavior: BehaviorProfile
    connections: Set[str] = field(default_factory=set)  # Connected node IDs
    joined_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def node_id(self) -> str:
        return self.identity.node_id

    @property
    def display_name(self) -> str:
        return self.identity.display_name

    @property
    def current_trust(self) -> float:
        return self.trust_state.current_trust

    @property
    def is_quarantined(self) -> bool:
        return self.trust_state.quarantined

    @property
    def is_adversarial(self) -> bool:
        return self.behavior.is_adversarial()

    @property
    def influence_score(self) -> float:
        return self.influence.normalized_influence

    def add_connection(self, other_node_id: str) -> None:
        """Add a connection to another node."""
        self.connections.add(other_node_id)

    def remove_connection(self, other_node_id: str) -> None:
        """Remove a connection to another node."""
        self.connections.discard(other_node_id)

    def is_connected_to(self, other_node_id: str) -> bool:
        """Check if connected to another node."""
        return other_node_id in self.connections

    def connection_count(self) -> int:
        """Get number of connections."""
        return len(self.connections)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of this node's state."""
        return {
            "node_id": self.node_id,
            "display_name": self.display_name,
            "current_trust": self.current_trust,
            "trust_tier": self.trust_state.get_trust_tier(),
            "quarantined": self.is_quarantined,
            "primary_domain": self.domain_spec.primary_domain.value,
            "influence_score": self.influence_score,
            "follower_count": self.influence.follower_count,
            "citation_count": self.influence.citation_count,
            "connection_count": self.connection_count(),
            "adversarial_mode": self.behavior.adversarial_mode,
            "adversarial_intensity": self.behavior.adversarial_intensity,
        }


class NodeRegistry:
    """Central registry for all nodes in the federation simulation.

    Manages node lifecycle, trust updates, influence calculations,
    and node lookup operations.
    """

    def __init__(self):
        self.nodes: Dict[str, FederatedNode] = {}
        self.identity_index: Dict[str, NodeIdentity] = {}
        self.trust_index: Dict[str, NodeTrustState] = {}
        self.influence_history: Dict[str, List[float]] = {}
        self.logger = logging.getLogger(__name__)

    def register_node(self, node: FederatedNode) -> None:
        """Register a new node in the federation."""
        if node.node_id in self.nodes:
            self.logger.warning(f"Node {node.node_id} already registered, updating")
            self.nodes[node.node_id] = node
        else:
            self.nodes[node.node_id] = node
            self.influence_history[node.node_id] = []

        self.identity_index[node.node_id] = node.identity
        self.trust_index[node.node_id] = node.trust_state

        self.logger.debug(
            f"Registered node {node.node_id} "
            f"(trust={node.current_trust:.2f}, domain={node.domain_spec.primary_domain.value})"
        )

    def get_node(self, node_id: str) -> Optional[FederatedNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_all_nodes(self) -> List[FederatedNode]:
        """Get all registered nodes."""
        return list(self.nodes.values())

    def get_active_nodes(self) -> List[FederatedNode]:
        """Get all non-quarantined nodes."""
        return [n for n in self.nodes.values() if not n.is_quarantined]

    def get_node_count(self) -> int:
        """Get total node count."""
        return len(self.nodes)

    def get_active_count(self) -> int:
        """Get active (non-quarantined) node count."""
        return sum(1 for n in self.nodes.values() if not n.is_quarantined)

    def update_trust(self, node_id: str, adjustment: float, reason: Optional[str] = None) -> bool:
        """Update trust score for a node."""
        node = self.get_node(node_id)
        if not node:
            self.logger.warning(f"Cannot update trust for unknown node {node_id}")
            return False

        old_trust = node.current_trust
        node.trust_state.apply_adjustment(adjustment)
        new_trust = node.current_trust

        self.logger.debug(
            f"Trust update for {node_id}: {old_trust:.3f} -> {new_trust:.3f} "
            f"(adjustment={adjustment:+.3f}, reason={reason})"
        )

        return True

    def apply_trust_decay(self, decay_rate: float = 0.01) -> Dict[str, float]:
        """Apply trust decay to all nodes.

        Returns dict of node_id -> old_trust
        """
        old_trusts = {}
        for node in self.get_all_nodes():
            old_trusts[node.node_id] = node.current_trust
            node.trust_state.decay(decay_rate)

        self.logger.debug(f"Applied trust decay ({decay_rate}) to {len(old_trusts)} nodes")
        return old_trusts

    def record_influence(self, node_id: str, influence: float) -> None:
        """Record influence score for a node."""
        if node_id not in self.influence_history:
            self.influence_history[node_id] = []
        self.influence_history[node_id].append(influence)

        # Update node's influence profile
        node = self.get_node(node_id)
        if node:
            node.influence.update_influence(influence)

    def get_influential_nodes(self, top_n: int = 5) -> List[FederatedNode]:
        """Get top N nodes by influence."""
        sorted_nodes = sorted(
            self.get_all_nodes(),
            key=lambda n: n.influence_score,
            reverse=True
        )
        return sorted_nodes[:top_n]

    def get_nodes_by_domain(self, domain: Domain) -> List[FederatedNode]:
        """Get nodes that specialize in a domain."""
        return [
            n for n in self.get_all_nodes()
            if n.domain_spec.is_specialist(domain)
        ]

    def get_nodes_by_trust_tier(self, tier: str) -> List[FederatedNode]:
        """Get nodes by trust tier."""
        return [
            n for n in self.get_all_nodes()
            if n.trust_state.get_trust_tier() == tier
        ]

    def get_adversarial_nodes(self) -> List[FederatedNode]:
        """Get all nodes in adversarial mode."""
        return [n for n in self.get_all_nodes() if n.is_adversarial]

    def get_nodes_by_coordination_group(self, group: str) -> List[FederatedNode]:
        """Get nodes in a specific coordination group."""
        return [
            n for n in self.get_all_nodes()
            if n.behavior.coordination_group == group
        ]

    def get_quarantined_nodes(self) -> List[FederatedNode]:
        """Get all quarantined nodes."""
        return [n for n in self.get_all_nodes() if n.is_quarantined]

    def unquarantine(self, node_id: str) -> bool:
        """Remove quarantine from a node."""
        node = self.get_node(node_id)
        if not node:
            return False

        node.trust_state.quarantined = False
        node.trust_state.quarantine_reason = None
        node.trust_state.quarantine_since = None

        self.logger.info(f"Unquarantined node {node_id}")
        return True

    def quarantine(self, node_id: str, reason: str = "Manual quarantine") -> bool:
        """Place a node in quarantine."""
        node = self.get_node(node_id)
        if not node:
            return False

        node.trust_state.quarantined = True
        node.trust_state.quarantine_reason = reason
        node.trust_state.quarantine_since = datetime.utcnow()

        self.logger.info(f"Quarantined node {node_id}: {reason}")
        return True

    def get_network_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the entire network."""
        nodes = self.get_all_nodes()

        if not nodes:
            return {
                "total_nodes": 0,
                "active_nodes": 0,
                "quarantined_nodes": 0,
                "adversarial_nodes": 0,
                "avg_trust": 0.0,
                "avg_influence": 0.0,
            }

        total_trust = sum(n.current_trust for n in nodes)
        total_influence = sum(n.influence_score for n in nodes)
        quarantined = sum(1 for n in nodes if n.is_quarantined)
        adversarial = sum(1 for n in nodes if n.is_adversarial)

        return {
            "total_nodes": len(nodes),
            "active_nodes": len(nodes) - quarantined,
            "quarantined_nodes": quarantined,
            "adversarial_nodes": adversarial,
            "avg_trust": total_trust / len(nodes),
            "avg_influence": total_influence / len(nodes),
            "trust_distribution": self._get_distribution(n.current_trust for n in nodes),
            "influence_distribution": self._get_distribution(n.influence_score for n in nodes),
        }

    def _get_distribution(self, values) -> Dict[str, int]:
        """Get distribution bucket counts."""
        buckets = {
            "very_low": 0,    # 0.0 - 0.2
            "low": 0,         # 0.2 - 0.4
            "medium": 0,      # 0.4 - 0.6
            "high": 0,        # 0.6 - 0.8
            "very_high": 0,   # 0.8 - 1.0
        }
        for v in values:
            if v < 0.2:
                buckets["very_low"] += 1
            elif v < 0.4:
                buckets["low"] += 1
            elif v < 0.6:
                buckets["medium"] += 1
            elif v < 0.8:
                buckets["high"] += 1
            else:
                buckets["very_high"] += 1
        return buckets


def create_node(
    node_id: str,
    display_name: str,
    domain: Domain,
    initial_trust: float = 0.5,
    claim_frequency: float = 1.0,
    adversarial_mode: Optional[str] = None,
    adversarial_intensity: float = 0.0,
) -> FederatedNode:
    """Factory function to create a new FederatedNode.

    Args:
        node_id: Unique node identifier
        display_name: Human-readable name
        domain: Primary domain specialization
        initial_trust: Starting trust score (0-1)
        claim_frequency: Claim generation multiplier
        adversarial_mode: Optional adversarial behavior mode
        adversarial_intensity: Intensity of adversarial behavior (0-1)

    Returns:
        Fully configured FederatedNode
    """
    now = datetime.utcnow()

    identity = NodeIdentity(
        node_id=node_id,
        display_name=display_name,
        public_key=f"pk_{node_id}",
        key_id=f"key_{node_id}",
        created_at=now,
    )

    trust_state = NodeTrustState(
        node_id=node_id,
        baseline_trust=initial_trust,
        current_trust=initial_trust,
    )

    domain_spec = DomainSpecialization(
        primary_domain=domain,
        secondary_domains=[],
    )

    influence = InfluenceProfile(
        node_id=node_id,
        raw_influence=initial_trust,
        normalized_influence=initial_trust,
    )

    behavior = BehaviorProfile(
        node_id=node_id,
        claim_frequency=claim_frequency,
    )

    if adversarial_mode:
        behavior.set_adversarial_mode(adversarial_mode, adversarial_intensity)

    return FederatedNode(
        identity=identity,
        trust_state=trust_state,
        domain_spec=domain_spec,
        influence=influence,
        behavior=behavior,
    )


def create_nodes_with_distribution(
    count: int,
    domains: Optional[List[Domain]] = None,
    trust_distribution: str = "uniform",  # uniform, normal, skewed
    adversarial_ratio: float = 0.0,
) -> List[FederatedNode]:
    """Create multiple nodes with specified distributions.

    Args:
        count: Number of nodes to create
        domains: List of domains to distribute (default: all domains)
        trust_distribution: How to distribute initial trust
        adversarial_ratio: Fraction of nodes that are adversarial

    Returns:
        List of FederatedNode instances
    """
    import random

    if domains is None:
        domains = list(Domain)

    nodes = []
    adversarial_count = int(count * adversarial_ratio)

    for i in range(count):
        node_id = f"node_{i:04d}"
        display_name = f"Node {i}"

        # Assign domain
        domain = random.choice(domains)

        # Assign initial trust
        if trust_distribution == "uniform":
            initial_trust = random.random()
        elif trust_distribution == "normal":
            initial_trust = min(1.0, max(0.0, random.gauss(0.5, 0.15)))
        elif trust_distribution == "skewed":
            # Beta distribution skewed toward higher trust
            initial_trust = random.betavariate(2, 1)
        else:
            initial_trust = 0.5

        # Check if adversarial
        is_adversarial = i < adversarial_count
        adversarial_mode = None
        adversarial_intensity = 0.0

        if is_adversarial:
            adversarial_mode = random.choice(["flood", "monoculture", "capture", "sybil"])
            adversarial_intensity = random.uniform(0.3, 0.8)

        node = create_node(
            node_id=node_id,
            display_name=display_name,
            domain=domain,
            initial_trust=initial_trust,
            adversarial_mode=adversarial_mode,
            adversarial_intensity=adversarial_intensity,
        )

        nodes.append(node)

    return nodes
