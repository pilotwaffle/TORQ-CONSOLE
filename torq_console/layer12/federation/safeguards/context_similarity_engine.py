"""
Context Similarity Engine

Phase 1B Hardening - Prevent context collapse and knowledge monoculture.

This engine analyzes federated claims for semantic clustering risks:
- Detects when too many similar claims arrive from the same source
- Identifies topic dominance patterns
- Flags over-represented semantic domains
- Recommends diversification when context collapse is imminent

Without this safeguard, a single node could flood the federation
with narrowly-focused claims, creating a "context monoculture" that
crowds out diverse perspectives and reduces the value of collective intelligence.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.types import FederatedArtifactPayload

logger = logging.getLogger(__name__)


# ============================================================================
# Similarity Analysis Types
# ============================================================================

class TopicCluster(BaseModel):
    """A cluster of semantically similar claims."""

    cluster_id: str = Field(..., description="Cluster identifier")
    dominant_keywords: list[str] = Field(
        default_factory=list,
        description="Key terms that define this cluster"
    )
    claim_count: int = Field(default=0, description="Number of claims in cluster")
    source_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Claims per source node"
    )
    earliest_seen: datetime | None = None
    latest_seen: datetime | None = None
    avg_confidence: float = Field(default=0.0, description="Average confidence in cluster")


class ContextRiskProfile(BaseModel):
    """Risk assessment for context collapse."""

    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Context collapse risk level"
    )
    dominant_clusters: list[TopicCluster] = Field(
        default_factory=list,
        description="Clusters that may be crowding out others"
    )
    diversity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Semantic diversity (1.0 = highly diverse)"
    )
    source_concentration: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How concentrated claims are from few sources"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actions to reduce context collapse risk"
    )


class SimilarityAnalysisResult(BaseModel):
    """Result of context similarity analysis."""

    artifact_id: str = Field(..., description="Artifact being analyzed")
    envelope_id: str = Field(..., description="Envelope ID")
    source_node_id: str = Field(..., description="Source node")

    # Cluster assignment
    assigned_cluster: str | None = Field(
        None,
        description="Cluster this claim was assigned to"
    )
    cluster_similarity: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Similarity to assigned cluster"
    )

    # Risk assessment
    risk_profile: ContextRiskProfile | None = None

    # Action recommendation
    should_warn: bool = Field(default=False, description="Warn about context collapse")
    should_throttle: bool = Field(default=False, description="Throttle this claim")

    # Analysis timestamp
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Similarity Engine Configuration
# ============================================================================

class SimilarityEngineConfig(BaseModel):
    """Configuration for context similarity analysis."""

    # Clustering thresholds
    min_similarity_for_cluster: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity to group claims in same cluster"
    )
    max_cluster_size: int = Field(
        50,
        ge=1,
        description="Maximum claims per cluster before flagging"
    )
    max_source_share_per_cluster: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Max share of cluster from single source"
    )

    # Risk thresholds
    diversity_threshold_low: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Below this = low diversity"
    )
    diversity_threshold_critical: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Below this = critical monoculture"
    )
    source_concentration_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Above this = source dominance detected"
    )

    # Analysis window
    analysis_window_hours: int = Field(
        24,
        ge=1,
        description="Hours to look back for clustering analysis"
    )

    # Keyword extraction (simple word frequency for now)
    min_keyword_length: int = Field(4, ge=1, description="Minimum keyword length")
    max_keywords_per_cluster: int = Field(5, ge=1, description="Keywords to track")


# ============================================================================
# Context Similarity Engine
# ============================================================================

class ContextSimilarityEngine:
    """
    Analyzes federated claims for context collapse risks.

    This safeguard operates AFTER eligibility filtering but
    BEFORE trust evaluation, providing early warning of
    semantic monoculture patterns.
    """

    def __init__(
        self,
        config: SimilarityEngineConfig | None = None,
    ):
        """
        Initialize the context similarity engine.

        Args:
            config: Engine configuration
        """
        self.config = config or SimilarityEngineConfig()
        self.logger = logging.getLogger(__name__)

        # Cluster storage
        self._clusters: dict[str, TopicCluster] = {}

        # Keyword index for similarity matching
        self._keyword_to_clusters: dict[str, set[str]] = defaultdict(set)

        # Per-node cluster tracking
        self._node_cluster_counts: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Statistics
        self._total_analyzed = 0
        self._total_warnings = 0
        self._total_throttled = 0

    def analyze_claim(
        self,
        artifact: FederatedArtifactPayload,
        envelope_id: str,
        source_node_id: str,
    ) -> SimilarityAnalysisResult:
        """
        Analyze a claim for context similarity risks.

        Args:
            artifact: The artifact payload to analyze
            envelope_id: Envelope ID
            source_node_id: Source node ID

        Returns:
            SimilarityAnalysisResult with risk assessment
        """
        self._total_analyzed += 1

        # Extract keywords from claim
        keywords = self._extract_keywords(artifact)

        # Find similar existing cluster
        cluster_id, similarity = self._find_similar_cluster(keywords, artifact.artifact_type)

        # Create or update cluster
        if cluster_id:
            cluster = self._update_cluster(cluster_id, artifact, source_node_id, keywords)
        else:
            cluster_id = self._create_cluster(artifact, source_node_id, keywords)
            cluster = self._clusters[cluster_id]
            similarity = 1.0  # New cluster = perfect match to itself

        # Assess context collapse risk
        risk_profile = self._assess_risk(source_node_id, cluster_id)

        # Determine actions
        should_warn = risk_profile.risk_level in ("medium", "high", "critical")
        should_throttle = risk_profile.risk_level == "critical"

        # Update statistics
        if should_warn:
            self._total_warnings += 1
        if should_throttle:
            self._total_throttled += 1

        result = SimilarityAnalysisResult(
            artifact_id=artifact.artifact_id,
            envelope_id=envelope_id,
            source_node_id=source_node_id,
            assigned_cluster=cluster_id,
            cluster_similarity=similarity,
            risk_profile=risk_profile,
            should_warn=should_warn,
            should_throttle=should_throttle,
        )

        self.logger.info(
            f"Similarity analysis for {artifact.artifact_id}: "
            f"cluster={cluster_id}, similarity={similarity:.2f}, "
            f"risk={risk_profile.risk_level}"
        )

        return result

    def _extract_keywords(
        self,
        artifact: FederatedArtifactPayload,
    ) -> list[str]:
        """
        Extract keywords from artifact for similarity matching.

        Args:
            artifact: Artifact to extract from

        Returns:
            List of normalized keywords
        """
        import re

        # Combine title and claim text
        text = f"{artifact.title} {artifact.claim_text}".lower()

        # Extract words (simple approach)
        words = re.findall(r'\b[a-z]+\b', text)

        # Filter by length and common stop words
        stop_words = {
            "the", "and", "that", "have", "for", "not", "with", "you",
            "this", "but", "his", "from", "they", "she", "her", "been",
            "than", "its", "were", "said", "each", "does", "their", "such"
        }

        keywords = [
            w for w in words
            if len(w) >= self.config.min_keyword_length
            and w not in stop_words
        ]

        # Include tags
        keywords.extend(artifact.tags)

        return list(set(keywords))

    def _find_similar_cluster(
        self,
        keywords: list[str],
        artifact_type: str,
    ) -> tuple[str | None, float]:
        """
        Find an existing cluster similar to the given keywords.

        Args:
            keywords: Keywords to match
            artifact_type: Type of artifact

        Returns:
            Tuple of (cluster_id, similarity_score)
        """
        if not keywords:
            return None, 0.0

        # Count cluster matches by keyword overlap
        cluster_matches: dict[str, int] = defaultdict(int)

        for keyword in keywords:
            for cluster_id in self._keyword_to_clusters.get(keyword, set()):
                cluster_matches[cluster_id] += 1

        if not cluster_matches:
            return None, 0.0

        # Find best match
        best_cluster_id = max(cluster_matches, key=cluster_matches.get)
        match_count = cluster_matches[best_cluster_id]

        # Calculate similarity (Jaccard-like)
        cluster = self._clusters.get(best_cluster_id)
        if not cluster:
            return None, 0.0

        cluster_keywords = set(cluster.dominant_keywords)
        keyword_set = set(keywords)

        intersection = len(cluster_keywords & keyword_set)
        union = len(cluster_keywords | keyword_set)

        similarity = intersection / union if union > 0 else 0.0

        if similarity >= self.config.min_similarity_for_cluster:
            return best_cluster_id, similarity

        return None, 0.0

    def _create_cluster(
        self,
        artifact: FederatedArtifactPayload,
        source_node_id: str,
        keywords: list[str],
    ) -> str:
        """Create a new topic cluster."""
        import uuid

        cluster_id = f"cluster_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        cluster = TopicCluster(
            cluster_id=cluster_id,
            dominant_keywords=keywords[:self.config.max_keywords_per_cluster],
            claim_count=1,
            source_distribution={source_node_id: 1},
            earliest_seen=now,
            latest_seen=now,
            avg_confidence=artifact.confidence,
        )

        self._clusters[cluster_id] = cluster
        self._node_cluster_counts[source_node_id][cluster_id] += 1

        # Update keyword index
        for keyword in keywords:
            self._keyword_to_clusters[keyword].add(cluster_id)

        return cluster_id

    def _update_cluster(
        self,
        cluster_id: str,
        artifact: FederatedArtifactPayload,
        source_node_id: str,
        keywords: list[str],
    ) -> TopicCluster:
        """Update an existing cluster with a new claim."""
        cluster = self._clusters[cluster_id]
        now = datetime.utcnow()

        # Update counts
        cluster.claim_count += 1
        cluster.source_distribution[source_node_id] = \
            cluster.source_distribution.get(source_node_id, 0) + 1
        cluster.latest_seen = now

        # Update average confidence
        cluster.avg_confidence = (
            (cluster.avg_confidence * (cluster.claim_count - 1) + artifact.confidence)
            / cluster.claim_count
        )

        # Update keywords (add new ones)
        for keyword in keywords:
            if keyword not in cluster.dominant_keywords:
                if len(cluster.dominant_keywords) < self.config.max_keywords_per_cluster:
                    cluster.dominant_keywords.append(keyword)
            self._keyword_to_clusters[keyword].add(cluster_id)

        # Update node tracking
        self._node_cluster_counts[source_node_id][cluster_id] += 1

        return cluster

    def _assess_risk(
        self,
        source_node_id: str,
        cluster_id: str,
    ) -> ContextRiskProfile:
        """
        Assess context collapse risk based on current state.

        Args:
            source_node_id: Node submitting the claim
            cluster_id: Cluster the claim belongs to

        Returns:
            ContextRiskProfile with risk assessment
        """
        cluster = self._clusters.get(cluster_id)
        if not cluster:
            return ContextRiskProfile(
                risk_level="low",
                dominant_clusters=[],
                diversity_score=1.0,
                source_concentration=0.0,
                recommendations=[],
            )

        # Calculate diversity score (inverse of concentration)
        diversity_score = self._calculate_diversity_score()

        # Calculate source concentration
        source_concentration = self._calculate_source_concentration()

        # Identify dominant clusters
        dominant_clusters = self._get_dominant_clusters()

        # Determine risk level
        risk_level = "low"
        recommendations: list[str] = []

        if diversity_score < self.config.diversity_threshold_critical:
            risk_level = "critical"
            recommendations.append("CRITICAL: Context monoculture detected")
            recommendations.append("Immediately throttle claims from dominant clusters")
            recommendations.append("Request diverse perspectives from underrepresented nodes")
        elif diversity_score < self.config.diversity_threshold_low:
            risk_level = "high"
            recommendations.append("WARNING: Low semantic diversity detected")
            recommendations.append("Encourage claims from different topic domains")
        elif source_concentration > self.config.source_concentration_threshold:
            risk_level = "medium"
            recommendations.append("CAUTION: High source concentration")
            recommendations.append("Distribute claims more evenly across nodes")

        # Check cluster size
        if cluster.claim_count > self.config.max_cluster_size:
            if risk_level == "low":
                risk_level = "medium"
            recommendations.append(
                f"Cluster {cluster_id} exceeds size threshold ({cluster.claim_count} claims)"
            )

        # Check source dominance within cluster
        if cluster.source_distribution:
            max_source_share = max(cluster.source_distribution.values()) / cluster.claim_count
            if max_source_share > self.config.max_source_share_per_cluster:
                if risk_level == "low":
                    risk_level = "medium"
                recommendations.append(
                    f"Single source dominates cluster {cluster_id} "
                    f"({max_source_share:.0%} of claims)"
                )

        return ContextRiskProfile(
            risk_level=risk_level,  # type: ignore
            dominant_clusters=dominant_clusters,
            diversity_score=diversity_score,
            source_concentration=source_concentration,
            recommendations=recommendations,
        )

    def _calculate_diversity_score(self) -> float:
        """
        Calculate semantic diversity across all clusters.

        Uses Shannon entropy normalized by cluster count.
        """
        if not self._clusters:
            return 1.0

        total_claims = sum(c.claim_count for c in self._clusters.values())
        if total_claims == 0:
            return 1.0

        # Calculate entropy
        import math
        entropy = 0.0
        for cluster in self._clusters.values():
            if cluster.claim_count > 0:
                p = cluster.claim_count / total_claims
                entropy -= p * math.log(p)

        # Normalize by max possible entropy (log of cluster count)
        max_entropy = math.log(len(self._clusters)) if len(self._clusters) > 1 else 1.0

        return entropy / max_entropy if max_entropy > 0 else 1.0

    def _calculate_source_concentration(self) -> float:
        """
        Calculate how concentrated claims are from few sources.

        Returns 1.0 if all claims from one source, 0.0 if perfectly distributed.
        """
        if not self._clusters:
            return 0.0

        # Aggregate source counts across all clusters
        source_totals: dict[str, int] = defaultdict(int)
        total_claims = 0

        for cluster in self._clusters.values():
            for source, count in cluster.source_distribution.items():
                source_totals[source] += count
                total_claims += count

        if total_claims == 0:
            return 0.0

        # Calculate Herfindahl-Hirschman Index (HHI)
        hhi = sum((count / total_claims) ** 2 for count in source_totals.values())

        return hhi

    def _get_dominant_clusters(self) -> list[TopicCluster]:
        """
        Get clusters that may be crowding out others.

        Returns clusters with size > 2x median.
        """
        if not self._clusters:
            return []

        sizes = [c.claim_count for c in self._clusters.values()]
        if not sizes:
            return []

        median_size = sorted(sizes)[len(sizes) // 2]
        threshold = median_size * 2

        return [
            c for c in self._clusters.values()
            if c.claim_count > threshold
        ]

    def get_statistics(self) -> dict:
        """Get engine statistics."""
        # Clean old clusters
        self._cleanup_old_clusters()

        return {
            "totalAnalyzed": self._total_analyzed,
            "totalWarnings": self._total_warnings,
            "totalThrottled": self._total_throttled,
            "activeClusters": len(self._clusters),
            "clusterDetails": [
                {
                    "clusterId": c.cluster_id,
                    "claimCount": c.claim_count,
                    "dominantKeywords": c.dominant_keywords,
                    "sourceDistribution": c.source_distribution,
                }
                for c in sorted(
                    self._clusters.values(),
                    key=lambda x: x.claim_count,
                    reverse=True
                )[:10]  # Top 10
            ],
        }

    def _cleanup_old_clusters(self) -> None:
        """Remove clusters outside the analysis window."""
        cutoff = datetime.utcnow() - timedelta(hours=self.config.analysis_window_hours)

        clusters_to_remove = [
            cluster_id
            for cluster_id, cluster in self._clusters.items()
            if cluster.latest_seen and cluster.latest_seen < cutoff
        ]

        for cluster_id in clusters_to_remove:
            cluster = self._clusters[cluster_id]

            # Remove from keyword index
            for keyword in cluster.dominant_keywords:
                self._keyword_to_clusters[keyword].discard(cluster_id)

            # Remove cluster
            del self._clusters[cluster_id]

            self.logger.debug(f"Cleaned up old cluster: {cluster_id}")


def create_context_similarity_engine(
    config: SimilarityEngineConfig | None = None,
) -> ContextSimilarityEngine:
    """
    Factory function to create a ContextSimilarityEngine.

    Args:
        config: Engine configuration

    Returns:
        Configured ContextSimilarityEngine instance
    """
    return ContextSimilarityEngine(config=config)
