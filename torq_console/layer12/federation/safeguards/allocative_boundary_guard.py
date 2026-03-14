"""
Allocative Boundary Guard

Phase 1B Hardening - Prevent authority and resource concentration.

This guard enforces fair allocative boundaries within the federation:
- Tracks resource allocation (claim acceptance, trust accrual) per node
- Detects dominance patterns where少数 nodes control majority of influence
- Enforces allocative fairness rules
- Prevents centralization of epistemic authority

Without this safeguard, a small number of high-trust nodes could
disproportionately influence the collective knowledge, creating
centralization risks and reducing the democratic nature of the federation.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.types import FederatedArtifactPayload

logger = logging.getLogger(__name__)


# ============================================================================
# Allocative Tracking Types
# ============================================================================

class NodeAllocativeProfile(BaseModel):
    """
    Profile tracking a node's allocative footprint.
    """

    node_id: str = Field(..., description="Node identifier")

    # Claim submission metrics
    total_submissions: int = Field(default=0, description="Total claims submitted")
    accepted_submissions: int = Field(default=0, description="Claims accepted for federation")
    rejected_submissions: int = Field(default=0, description="Claims rejected")

    # Influence metrics
    total_trust_accrued: float = Field(default=0.0, description="Total trust score accrued")
    avg_trust_score: float = Field(default=0.0, description="Average trust score")

    # Domain dominance
    domain_leadership: dict[str, int] = Field(
        default_factory=dict,
        description="Count of claims where this node is domain leader"
    )

    # Temporal tracking
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    # Quota tracking
    current_acceptance_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Current acceptance rate (may be throttled)"
    )


class AllocativeSnapshot(BaseModel):
    """
    Snapshot of allocative distribution across the federation.
    """

    total_nodes: int = Field(..., description="Total active nodes")
    total_submissions: int = Field(..., description="Total claims submitted")
    total_accepted: int = Field(..., description="Total claims accepted")

    # Concentration metrics
    gini_coefficient: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Gini coefficient (0 = perfect equality, 1 = perfect inequality)"
    )
    herfindahl_index: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Herfindahl-Hirschman Index (lower = more distributed)"
    )
    top_node_concentration: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Share of submissions from top node"
    )
    top_3_concentration: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Share of submissions from top 3 nodes"
    )

    # Dominant nodes
    dominant_nodes: list[str] = Field(
        default_factory=list,
        description="Nodes exceeding allocative thresholds"
    )


class AllocativeDecision(BaseModel):
    """
    Decision on whether to accept a claim based on allocative boundaries.
    """

    artifact_id: str = Field(..., description="Artifact being evaluated")
    node_id: str = Field(..., description="Submitting node")

    # Decision
    is_allowed: bool = Field(..., description="Whether claim is allowed within allocative bounds")
    throttle_factor: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Throttle factor (1.0 = full acceptance, 0.0 = full rejection)"
    )

    # Rationale
    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for the decision"
    )

    # Node's allocative status
    node_share: float = Field(..., description="Node's current share of total submissions")
    node_rank: int = Field(..., description="Node's rank by submissions")
    is_dominant: bool = Field(default=False, description="Node is flagged as dominant")

    # Recommendation
    recommendation: Literal["accept", "throttle", "reject"] = Field(
        ...,
        description="Recommended action"
    )


# ============================================================================
# Allocative Boundary Configuration
# ============================================================================

class AllocativeBoundaryConfig(BaseModel):
    """Configuration for allocative boundary enforcement."""

    # Concentration thresholds
    max_node_share: float = Field(
        0.4,
        ge=0.0,
        le=1.0,
        description="Max share of total submissions from single node"
    )
    max_top_3_share: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Max combined share from top 3 nodes"
    )
    max_gini_coefficient: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Max Gini coefficient before intervention"
    )

    # Dominance thresholds
    dominance_threshold: float = Field(
        2.0,
        ge=1.0,
        description="Node dominance = share / average_share (higher = more dominant)"
    )
    dominant_node_throttle: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Throttle factor for dominant nodes"
    )

    # Domain leadership limits
    max_domain_leadership_share: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Max share of claims in a domain from single node"
    )

    # Analysis window
    analysis_window_hours: int = Field(
        24,
        ge=1,
        description="Hours to look back for allocative analysis"
    )

    # Minimum activity thresholds
    min_node_activity: int = Field(
        1,
        ge=0,
        description="Min submissions for node to be considered active"
    )


# ============================================================================
# Allocative Boundary Guard
# ============================================================================

class AllocativeBoundaryGuard:
    """
    Enforces allocative boundaries to prevent centralization.

    This guard operates AFTER eligibility filtering but
    influences the final accept/reject decision.

    Unlike other safeguards that focus on CONTENT quality,
    this focuses on DISTRIBUTION fairness across nodes.
    """

    def __init__(
        self,
        config: AllocativeBoundaryConfig | None = None,
    ):
        """
        Initialize the allocative boundary guard.

        Args:
            config: Guard configuration
        """
        self.config = config or AllocativeBoundaryConfig()
        self.logger = logging.getLogger(__name__)

        # Node profiles
        self._node_profiles: dict[str, NodeAllocativeProfile] = {}

        # Domain tracking
        self._domain_claims: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Statistics
        self._total_evaluated = 0
        self._total_accepted = 0
        self._total_throttled = 0
        self._total_rejected = 0

    def evaluate_claim(
        self,
        artifact: FederatedArtifactPayload,
        envelope_id: str,
        source_node_id: str,
        trust_score: float = 0.5,
    ) -> AllocativeDecision:
        """
        Evaluate whether a claim is within allocative boundaries.

        Args:
            artifact: The artifact payload to evaluate
            envelope_id: Envelope ID
            source_node_id: Source node ID
            trust_score: Node's current trust score

        Returns:
            AllocativeDecision with allowance and throttle factor
        """
        self._total_evaluated += 1

        # Get or create node profile
        profile = self._get_or_create_profile(source_node_id)

        # Calculate current allocative snapshot
        snapshot = self._calculate_snapshot()

        # Determine node's position
        node_share = self._calculate_node_share(source_node_id)
        node_rank = self._get_node_rank(source_node_id)
        is_dominant = self._is_dominant_node(source_node_id, snapshot)

        # Check domain leadership
        domain = self._infer_domain(artifact)
        domain_leadership_share = self._calculate_domain_leadership(
            source_node_id, domain
        )

        # Build decision
        reasons: list[str] = []
        is_allowed = True
        throttle_factor = 1.0
        recommendation: Literal["accept", "throttle", "reject"] = "accept"

        # Check concentration limits
        if node_share > self.config.max_node_share:
            is_allowed = False
            recommendation = "reject"
            reasons.append(
                f"Node exceeds maximum share: {node_share:.1%} > {self.config.max_node_share:.1%}"
            )

        # Check dominance
        if is_dominant and recommendation != "reject":
            throttle_factor = self.config.dominant_node_throttle
            recommendation = "throttle"
            reasons.append(
                f"Node is dominant (rank {node_rank}/{snapshot.total_nodes}, share {node_share:.1%})"
            )

        # Check top-3 concentration
        if snapshot.top_3_concentration > self.config.max_top_3_share:
            # If this node is in the top 3, throttle
            if node_rank <= 3:
                if recommendation != "reject":
                    throttle_factor = min(throttle_factor, 0.7)
                    recommendation = "throttle"
                    reasons.append(
                        f"Top-3 concentration high ({snapshot.top_3_concentration:.1%}), throttling"
                    )

        # Check Gini coefficient
        if snapshot.gini_coefficient > self.config.max_gini_coefficient:
            if is_dominant:
                if recommendation != "reject":
                    throttle_factor = min(throttle_factor, 0.5)
                    recommendation = "throttle"
                    reasons.append(
                        f"High inequality detected (Gini: {snapshot.gini_coefficient:.2f}), throttling dominant nodes"
                    )

        # Check domain leadership
        if domain_leadership_share > self.config.max_domain_leadership_share:
            if recommendation != "reject":
                throttle_factor = min(throttle_factor, 0.6)
                recommendation = "throttle"
                reasons.append(
                    f"Node leads domain '{domain}' with {domain_leadership_share:.1%} share, throttling"
                )

        # Add positive feedback if allowed
        if recommendation == "accept":
            reasons.append(f"Within allocative boundaries (share: {node_share:.1%})")

        # Update profile if allowed
        if is_allowed:
            profile.total_submissions += 1
            profile.last_seen = datetime.utcnow()
            if recommendation != "reject":
                profile.accepted_submissions += 1
                self._domain_claims[domain][source_node_id] += 1
            else:
                profile.rejected_submissions += 1

        # Update statistics
        if recommendation == "accept":
            self._total_accepted += 1
        elif recommendation == "throttle":
            self._total_throttled += 1
        else:
            self._total_rejected += 1

        decision = AllocativeDecision(
            artifact_id=artifact.artifact_id,
            node_id=source_node_id,
            is_allowed=is_allowed,
            throttle_factor=throttle_factor,
            reasons=reasons,
            node_share=node_share,
            node_rank=node_rank,
            is_dominant=is_dominant,
            recommendation=recommendation,
        )

        self.logger.info(
            f"Allocative decision for {artifact.artifact_id}: "
            f"allowed={is_allowed}, throttle={throttle_factor:.2f}, "
            f"recommendation={recommendation}"
        )

        return decision

    def _get_or_create_profile(self, node_id: str) -> NodeAllocativeProfile:
        """Get existing node profile or create new one."""
        if node_id not in self._node_profiles:
            now = datetime.utcnow()
            self._node_profiles[node_id] = NodeAllocativeProfile(
                node_id=node_id,
                first_seen=now,
                last_seen=now,
            )
        return self._node_profiles[node_id]

    def _calculate_snapshot(self) -> AllocativeSnapshot:
        """Calculate current allocative snapshot across all nodes."""
        active_nodes = [
            p for p in self._node_profiles.values()
            if p.total_submissions >= self.config.min_node_activity
        ]

        if not active_nodes:
            return AllocativeSnapshot(
                total_nodes=0,
                total_submissions=0,
                total_accepted=0,
                gini_coefficient=0.0,
                herfindahl_index=0.0,
                top_node_concentration=0.0,
                top_3_concentration=0.0,
                dominant_nodes=[],
            )

        total_submissions = sum(p.total_submissions for p in active_nodes)
        total_accepted = sum(p.accepted_submissions for p in active_nodes)

        if total_submissions == 0:
            return AllocativeSnapshot(
                total_nodes=len(active_nodes),
                total_submissions=0,
                total_accepted=0,
                gini_coefficient=0.0,
                herfindahl_index=0.0,
                top_node_concentration=0.0,
                top_3_concentration=0.0,
                dominant_nodes=[],
            )

        # Calculate shares
        shares = [p.total_submissions / total_submissions for p in active_nodes]
        shares_sorted = sorted(shares, reverse=True)

        # Gini coefficient
        n = len(shares)
        gini = sum((2 * i - n - 1) * s for i, s in enumerate(sorted(shares), 1))
        gini /= (n * sum(shares)) if sum(shares) > 0 else 1
        gini = abs(gini)

        # Herfindahl-Hirschman Index
        hhi = sum(s ** 2 for s in shares)

        # Top concentrations
        top_node_concentration = shares_sorted[0] if shares_sorted else 0.0
        top_3_concentration = sum(shares_sorted[:3]) if len(shares_sorted) >= 3 else sum(shares_sorted)

        # Identify dominant nodes
        avg_share = 1.0 / len(active_nodes) if active_nodes else 0.0
        dominant_nodes = [
            p.node_id
            for p in active_nodes
            if (p.total_submissions / total_submissions) > (avg_share * self.config.dominance_threshold)
        ]

        return AllocativeSnapshot(
            total_nodes=len(active_nodes),
            total_submissions=total_submissions,
            total_accepted=total_accepted,
            gini_coefficient=abs(gini),  # Ensure non-negative
            herfindahl_index=hhi,
            top_node_concentration=top_node_concentration,
            top_3_concentration=top_3_concentration,
            dominant_nodes=dominant_nodes,
        )

    def _calculate_node_share(self, node_id: str) -> float:
        """Calculate node's share of total submissions."""
        profile = self._node_profiles.get(node_id)
        if not profile or profile.total_submissions == 0:
            return 0.0

        total_submissions = sum(
            p.total_submissions
            for p in self._node_profiles.values()
            if p.total_submissions >= self.config.min_node_activity
        )

        if total_submissions == 0:
            return 0.0

        return profile.total_submissions / total_submissions

    def _get_node_rank(self, node_id: str) -> int:
        """Get node's rank by submissions (1 = highest)."""
        submissions = [
            (p.node_id, p.total_submissions)
            for p in self._node_profiles.values()
            if p.total_submissions >= self.config.min_node_activity
        ]

        if not submissions:
            return 0

        submissions_sorted = sorted(submissions, key=lambda x: x[1], reverse=True)

        for rank, (nid, _) in enumerate(submissions_sorted, 1):
            if nid == node_id:
                return rank

        return len(submissions_sorted) + 1

    def _is_dominant_node(self, node_id: str, snapshot: AllocativeSnapshot) -> bool:
        """Check if node is dominant."""
        return node_id in snapshot.dominant_nodes

    def _infer_domain(self, artifact: FederatedArtifactPayload) -> str:
        """Infer domain from artifact (simplified)."""
        # Use first tag or infer from title
        if artifact.tags:
            return artifact.tags[0].lower()

        # Simple keyword matching
        text = artifact.title.lower()
        if "security" in text or "auth" in text:
            return "security"
        if "performance" in text or "speed" in text:
            return "performance"
        if "scale" in text or "load" in text:
            return "scalability"

        return "general"

    def _calculate_domain_leadership(self, node_id: str, domain: str) -> float:
        """Calculate node's leadership share in a domain."""
        domain_claims = self._domain_claims.get(domain, {})

        if not domain_claims:
            return 0.0

        total = sum(domain_claims.values())
        node_share = domain_claims.get(node_id, 0)

        return node_share / total if total > 0 else 0.0

    def get_statistics(self) -> dict:
        """Get guard statistics."""
        snapshot = self._calculate_snapshot()

        # Clean old nodes
        self._cleanup_old_nodes()

        return {
            "totalEvaluated": self._total_evaluated,
            "totalAccepted": self._total_accepted,
            "totalThrottled": self._total_throttled,
            "totalRejected": self._total_rejected,
            "acceptanceRate": (
                self._total_accepted / max(self._total_evaluated, 1)
            ),
            "snapshot": {
                "totalNodes": snapshot.total_nodes,
                "totalSubmissions": snapshot.total_submissions,
                "giniCoefficient": snapshot.gini_coefficient,
                "herfindahlIndex": snapshot.herfindahl_index,
                "topNodeConcentration": snapshot.top_node_concentration,
                "top3Concentration": snapshot.top_3_concentration,
                "dominantNodes": snapshot.dominant_nodes,
            },
            "nodeProfiles": [
                {
                    "nodeId": p.node_id,
                    "totalSubmissions": p.total_submissions,
                    "acceptedSubmissions": p.accepted_submissions,
                    "rejectionRate": (
                        p.rejected_submissions / max(p.total_submissions, 1)
                    ),
                    "avgTrustScore": p.avg_trust_score,
                }
                for p in sorted(
                    self._node_profiles.values(),
                    key=lambda x: x.total_submissions,
                    reverse=True
                )[:20]  # Top 20
            ],
        }

    def _cleanup_old_nodes(self) -> None:
        """Remove inactive nodes outside the analysis window."""
        cutoff = datetime.utcnow() - timedelta(hours=self.config.analysis_window_hours)

        nodes_to_remove = [
            node_id
            for node_id, profile in self._node_profiles.items()
            if profile.last_seen and profile.last_seen < cutoff
        ]

        for node_id in nodes_to_remove:
            del self._node_profiles[node_id]
            self.logger.debug(f"Cleaned up inactive node: {node_id}")

    def get_node_allocative_report(self, node_id: str) -> dict:
        """
        Get detailed allocative report for a specific node.

        Args:
            node_id: Node to report on

        Returns:
            Detailed allocative report
        """
        profile = self._node_profiles.get(node_id)

        if not profile:
            return {
                "nodeId": node_id,
                "error": "Node not found",
            }

        snapshot = self._calculate_snapshot()

        return {
            "nodeId": node_id,
            "share": self._calculate_node_share(node_id),
            "rank": self._get_node_rank(node_id),
            "isDominant": node_id in snapshot.dominant_nodes,
            "submissions": profile.total_submissions,
            "accepted": profile.accepted_submissions,
            "rejected": profile.rejected_submissions,
            "acceptanceRate": (
                profile.accepted_submissions / max(profile.total_submissions, 1)
            ),
            "domainLeadership": {
                domain: self._calculate_domain_leadership(node_id, domain)
                for domain in list(self._domain_claims.keys())[:10]
            },
        }


def create_allocative_boundary_guard(
    config: AllocativeBoundaryConfig | None = None,
) -> AllocativeBoundaryGuard:
    """
    Factory function to create an AllocativeBoundaryGuard.

    Args:
        config: Guard configuration

    Returns:
        Configured AllocativeBoundaryGuard instance
    """
    return AllocativeBoundaryGuard(config=config)
