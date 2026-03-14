"""
Plurality Preservation Rules

Phase 1B Hardening - Prevent knowledge monoculture and minority opinion loss.

This engine enforces viewpoint diversity within the federation:
- Detects emerging consensus that may crowd out minority views
- Flags when similar perspectives dominate topic domains
- Enforces diversity thresholds for federated content
- Tracks perspective distribution across the knowledge graph

Without this safeguard, the federation could develop a "knowledge monoculture"
where dominant consensus crowds out valuable minority perspectives, reducing
the epistemic diversity that makes collective intelligence valuable.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.types import FederatedArtifactPayload

logger = logging.getLogger(__name__)


# ============================================================================
# Perspective Tracking
# ============================================================================

class PerspectiveSignature(BaseModel):
    """
    A semantic signature of a claim's perspective.

    Used to group similar viewpoints without exact matching.
    """

    perspective_id: str = Field(..., description="Unique perspective identifier")
    semantic_hash: str = Field(..., description="Hash of semantic content")
    stance_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords that indicate stance/position"
    )
    topic_domain: str = Field(..., description="Topic domain (e.g., 'security', 'performance')")
    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        default="neutral",
        description="General sentiment of perspective"
    )


class PerspectiveCluster(BaseModel):
    """A cluster of claims sharing similar perspectives."""

    perspective_id: str = Field(..., description="Perspective identifier")
    topic_domain: str = Field(..., description="Topic domain")
    claim_count: int = Field(default=0, description="Number of claims in this perspective")
    source_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Claims per source node"
    )
    avg_confidence: float = Field(default=0.0, description="Average confidence")
    earliest_seen: datetime | None = None
    latest_seen: datetime | None = None
    stance_summary: str = Field(default="", description="Summary of stance")


class ContradictionReport(BaseModel):
    """Report of contradiction within a topic domain."""

    domain: str = Field(..., description="Topic domain with contradiction")
    conflicting_perspectives: list[str] = Field(
        default_factory=list,
        description="IDs of conflicting perspectives"
    )
    contradiction_count: int = Field(default=0, description="Number of contradictions detected")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="low",
        description="Contradiction severity"
    )


# ============================================================================
# Plurality Assessment Types
# ============================================================================

class PluralityMetrics(BaseModel):
    """Metrics assessing viewpoint diversity."""

    perspective_count: int = Field(
        ...,
        description="Number of distinct perspectives"
    )
    shannon_diversity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Shannon entropy-based diversity (1.0 = maximally diverse)"
    )
    dominant_perspective_share: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Share of claims in largest perspective (lower = better)"
    )
    minority_perspective_count: int = Field(
        ...,
        description="Number of minority perspectives (<10% share)"
    )
    at_risk_perspectives: list[str] = Field(
        default_factory=list,
        description="Perspectives at risk of being lost"
    )


class PluralityAssessment(BaseModel):
    """Assessment of plurality for a claim or domain."""

    plurality_level: Literal["healthy", "concerning", "at_risk", "monoculture"] = Field(
        ...,
        description="Overall plurality health"
    )
    metrics: PluralityMetrics = Field(..., description="Diversity metrics")
    contradictions: list[ContradictionReport] = Field(
        default_factory=list,
        description="Active contradictions"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actions to preserve plurality"
    )
    should_warn: bool = Field(default=False, description="Warn about plurality loss")
    should_throttle: bool = Field(default=False, description="Throttle dominant perspectives")


class PluralityAnalysisResult(BaseModel):
    """Result of plurality preservation analysis."""

    artifact_id: str = Field(..., description="Artifact being analyzed")
    envelope_id: str = Field(..., description="Envelope ID")
    source_node_id: str = Field(..., description="Source node")

    # Perspective assignment
    assigned_perspective: str | None = Field(
        None,
        description="Perspective this claim was assigned to"
    )

    # Plurality assessment
    assessment: PluralityAssessment | None = None

    # Topic domain
    topic_domain: str = Field(..., description="Assigned topic domain")

    # Analysis timestamp
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Plurality Preservation Configuration
# ============================================================================

class PluralityPreservationConfig(BaseModel):
    """Configuration for plurality preservation rules."""

    # Diversity thresholds
    min_perspective_count: int = Field(
        3,
        ge=1,
        description="Minimum distinct perspectives per domain"
    )
    max_dominant_share: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Max share of single perspective before warning"
    )
    critical_dominant_share: float = Field(
        0.8,
        ge=0.0,
        le=1.0,
        description="Max share before throttling dominant perspectives"
    )
    min_diversity_score: float = Field(
        0.4,
        ge=0.0,
        le=1.0,
        description="Minimum Shannon diversity score"
    )

    # Minority protection
    minority_threshold: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Share below which a perspective is 'minority'"
    )
    at_risk_threshold: int = Field(
        5,
        ge=1,
        description="Claims below which a perspective is at risk of loss"
    )

    # Contradiction handling
    enable_contradiction_tracking: bool = Field(
        True,
        description="Track contradictions as healthy plurality signal"
    )
    max_contradiction_severity: Literal["low", "medium", "high", "critical"] = Field(
        "medium",
        description="Max contradiction severity before flagging"
    )

    # Analysis window
    analysis_window_hours: int = Field(
        24,
        ge=1,
        description="Hours to look back for plurality analysis"
    )


# ============================================================================
# Plurality Preservation Engine
# ============================================================================

class PluralityPreservationRules:
    """
    Enforces viewpoint diversity and prevents knowledge monoculture.

    This safeguard operates alongside the ContextSimilarityEngine but
    focuses on PERSPECTIVE diversity rather than semantic similarity.

    Two claims can be semantically similar but have different perspectives
    (e.g., "security is critical" vs "security is optional" are about
    security but represent opposing viewpoints).
    """

    def __init__(
        self,
        config: PluralityPreservationConfig | None = None,
    ):
        """
        Initialize the plurality preservation engine.

        Args:
            config: Engine configuration
        """
        self.config = config or PluralityPreservationConfig()
        self.logger = logging.getLogger(__name__)

        # Perspective storage per domain
        self._perspectives: dict[str, dict[str, PerspectiveCluster]] = defaultdict(dict)

        # Contradiction tracking per domain
        self._contradictions: dict[str, list[ContradictionReport]] = defaultdict(list)

        # Statistics
        self._total_analyzed = 0
        self._total_warnings = 0
        self._total_throttled = 0

    def analyze_claim(
        self,
        artifact: FederatedArtifactPayload,
        envelope_id: str,
        source_node_id: str,
    ) -> PluralityAnalysisResult:
        """
        Analyze a claim for plurality preservation.

        Args:
            artifact: The artifact payload to analyze
            envelope_id: Envelope ID
            source_node_id: Source node ID

        Returns:
            PluralityAnalysisResult with plurality assessment
        """
        self._total_analyzed += 1

        # Extract perspective signature
        signature = self._extract_perspective_signature(artifact)

        # Get or create perspective cluster
        perspective_id = signature.perspective_id
        domain = signature.topic_domain

        if domain not in self._perspectives:
            self._perspectives[domain] = {}

        if perspective_id not in self._perspectives[domain]:
            self._perspectives[domain][perspective_id] = PerspectiveCluster(
                perspective_id=perspective_id,
                topic_domain=domain,
                claim_count=0,
                stance_summary=signature.stance_keywords[0] if signature.stance_keywords else "",
            )

        # Update cluster
        cluster = self._perspectives[domain][perspective_id]
        cluster.claim_count += 1
        cluster.source_distribution[source_node_id] = \
            cluster.source_distribution.get(source_node_id, 0) + 1
        cluster.avg_confidence = (
            (cluster.avg_confidence * (cluster.claim_count - 1) + artifact.confidence)
            / cluster.claim_count
        )

        now = datetime.utcnow()
        if cluster.earliest_seen is None:
            cluster.earliest_seen = now
        cluster.latest_seen = now

        # Assess plurality for this domain
        assessment = self._assess_plurality(domain, perspective_id)

        # Update statistics
        if assessment.should_warn:
            self._total_warnings += 1
        if assessment.should_throttle:
            self._total_throttled += 1

        result = PluralityAnalysisResult(
            artifact_id=artifact.artifact_id,
            envelope_id=envelope_id,
            source_node_id=source_node_id,
            assigned_perspective=perspective_id,
            assessment=assessment,
            topic_domain=domain,
        )

        self.logger.info(
            f"Plurality analysis for {artifact.artifact_id}: "
            f"domain={domain}, perspective={perspective_id}, "
            f"plurality={assessment.plurality_level}"
        )

        return result

    def _extract_perspective_signature(
        self,
        artifact: FederatedArtifactPayload,
    ) -> PerspectiveSignature:
        """
        Extract perspective signature from artifact.

        The signature captures the CLAIM'S STANCE on a topic, not just
        the topic itself. This allows us to track diverse perspectives
        on the same topic.

        Args:
            artifact: Artifact to analyze

        Returns:
            PerspectiveSignature with stance and domain
        """
        import hashlib
        import re

        # Determine topic domain from tags and content
        domain = self._determine_topic_domain(artifact)

        # Extract stance keywords
        title_lower = artifact.title.lower()
        claim_lower = artifact.claim_text.lower()

        # Look for stance indicators
        stance_patterns = {
            "affirmative": ["should", "must", "essential", "critical", "important", "always"],
            "negative": ["should not", "never", "avoid", "dangerous", "risky", "harmful"],
            "conditional": ["depends", "context", "sometimes", "may", "might", "consider"],
            "neutral": ["is", "are", "can", "will", "does", "has"],
        }

        detected_stance = "neutral"
        stance_keywords = []

        for stance, patterns in stance_patterns.items():
            for pattern in patterns:
                if pattern in claim_lower or pattern in title_lower:
                    if stance != detected_stance:
                        stance_keywords.append(pattern)

        if stance_keywords:
            if any(w in claim_lower for w in stance_patterns["affirmative"]):
                detected_stance = "affirmative"
            elif any(w in claim_lower for w in stance_patterns["negative"]):
                detected_stance = "negative"
            elif any(w in claim_lower for w in stance_patterns["conditional"]):
                detected_stance = "conditional"

        # Determine sentiment
        positive_words = ["good", "great", "excellent", "effective", "success", "benefit"]
        negative_words = ["bad", "poor", "failure", "problem", "issue", "risk"]

        positive_count = sum(1 for w in positive_words if w in claim_lower)
        negative_count = sum(1 for w in negative_words if w in claim_lower)

        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Create semantic hash (stance + domain)
        semantic_content = f"{domain}:{detected_stance}:{artifact.artifact_type}"
        semantic_hash = hashlib.sha256(semantic_content.encode()).hexdigest()[:12]

        # Create perspective ID
        perspective_id = f"{domain}_{detected_stance}_{semantic_hash}"

        return PerspectiveSignature(
            perspective_id=perspective_id,
            semantic_hash=semantic_hash,
            stance_keywords=stance_keywords[:3],
            topic_domain=domain,
            sentiment=sentiment,  # type: ignore
        )

    def _determine_topic_domain(
        self,
        artifact: FederatedArtifactPayload,
    ) -> str:
        """
        Determine the topic domain for an artifact.

        Args:
            artifact: Artifact to analyze

        Returns:
            Topic domain string
        """
        # Domain keywords
        domain_keywords = {
            "security": ["security", "auth", "authentication", "encryption", "access", "permission"],
            "performance": ["performance", "speed", "latency", "optimization", "fast", "slow"],
            "scalability": ["scale", "scalability", "load", "capacity", "growth", "distributed"],
            "usability": ["usability", "ux", "user", "interface", "experience", "design"],
            "reliability": ["reliability", "availability", "uptime", "fault", "resilient", "stable"],
            "cost": ["cost", "price", "budget", "expensive", "cheap", "resource"],
            "architecture": ["architecture", "design", "structure", "pattern", "component"],
            "data": ["data", "database", "storage", "query", "model", "schema"],
        }

        text = f"{artifact.title} {artifact.claim_text} {' '.join(artifact.tags)}".lower()

        # Check each domain
        best_domain = "general"
        best_match = 0

        for domain, keywords in domain_keywords.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > best_match:
                best_match = matches
                best_domain = domain

        return best_domain

    def _assess_plurality(
        self,
        domain: str,
        perspective_id: str,
    ) -> PluralityAssessment:
        """
        Assess plurality health for a domain.

        Args:
            domain: Topic domain to assess
            perspective_id: Perspective being analyzed

        Returns:
            PluralityAssessment with recommendations
        """
        perspectives = self._perspectives.get(domain, {})

        if not perspectives:
            return PluralityAssessment(
                plurality_level="healthy",
                metrics=PluralityMetrics(
                    perspective_count=0,
                    shannon_diversity=1.0,
                    dominant_perspective_share=0.0,
                    minority_perspective_count=0,
                    at_risk_perspectives=[],
                ),
                contradictions=[],
                recommendations=[],
                should_warn=False,
                should_throttle=False,
            )

        # Calculate metrics
        total_claims = sum(p.claim_count for p in perspectives.values())
        perspective_count = len(perspectives)

        # Shannon diversity
        import math
        shannon_diversity = 0.0
        if total_claims > 0:
            for p in perspectives.values():
                if p.claim_count > 0:
                    prob = p.claim_count / total_claims
                    shannon_diversity -= prob * math.log(prob)
            # Normalize
            max_entropy = math.log(perspective_count) if perspective_count > 1 else 1.0
            shannon_diversity = shannon_diversity / max_entropy if max_entropy > 0 else 0.0

        # Dominant perspective share
        max_claims = max((p.claim_count for p in perspectives.values()), default=0)
        dominant_share = max_claims / total_claims if total_claims > 0 else 0.0

        # Minority perspectives
        minority_perspectives = [
            pid for pid, p in perspectives.items()
            if total_claims > 0 and (p.claim_count / total_claims) < self.config.minority_threshold
        ]

        # At-risk perspectives (low claim count)
        at_risk = [
            pid for pid, p in perspectives.items()
            if p.claim_count < self.config.at_risk_threshold
        ]

        metrics = PluralityMetrics(
            perspective_count=perspective_count,
            shannon_diversity=shannon_diversity,
            dominant_perspective_share=dominant_share,
            minority_perspective_count=len(minority_perspectives),
            at_risk_perspectives=at_risk,
        )

        # Determine plurality level
        plurality_level = "healthy"
        recommendations: list[str] = []
        should_warn = False
        should_throttle = False

        if perspective_count < self.config.min_perspective_count:
            plurality_level = "monoculture"
            should_warn = True
            should_throttle = True
            recommendations.append(
                f"CRITICAL: Only {perspective_count} perspective(s) in {domain} domain. "
                f"Minimum {self.config.min_perspective_count} required."
            )
        elif dominant_share > self.config.critical_dominant_share:
            plurality_level = "at_risk"
            should_warn = True
            should_throttle = True
            recommendations.append(
                f"CRITICAL: Single perspective dominates {dominant_share:.0%} of {domain} claims"
            )
        elif dominant_share > self.config.max_dominant_share:
            plurality_level = "concerning"
            should_warn = True
            recommendations.append(
                f"WARNING: Dominant perspective has {dominant_share:.0%} share in {domain}"
            )
        elif shannon_diversity < self.config.min_diversity_score:
            plurality_level = "concerning"
            should_warn = True
            recommendations.append(
                f"WARNING: Low diversity score ({shannon_diversity:.2f}) in {domain}"
            )

        # Check for minority perspective loss
        if at_risk:
            plurality_level = max(plurality_level, "concerning", key=lambda x: [
                "healthy", "concerning", "at_risk", "monoculture"
            ].index(x))
            recommendations.append(
                f"{len(at_risk)} perspective(s) at risk of loss in {domain}"
            )

        # Add positive note if healthy
        if plurality_level == "healthy":
            recommendations.append(f"Good perspective diversity in {domain} domain")

        # Get contradictions for domain
        contradictions = self._contradictions.get(domain, [])

        return PluralityAssessment(
            plurality_level=plurality_level,  # type: ignore
            metrics=metrics,
            contradictions=contradictions,
            recommendations=recommendations,
            should_warn=should_warn,
            should_throttle=should_throttle,
        )

    def record_contradiction(
        self,
        domain: str,
        perspective_a: str,
        perspective_b: str,
        severity: Literal["low", "medium", "high", "critical"] = "medium",
    ) -> None:
        """
        Record a contradiction between two perspectives.

        Contradictions are HEALTHY for plurality - they indicate
        diverse viewpoints exist. We track them but don't suppress.

        Args:
            domain: Topic domain
            perspective_a: First perspective ID
            perspective_b: Second perspective ID
            severity: Contradiction severity
        """
        report = ContradictionReport(
            domain=domain,
            conflicting_perspectives=[perspective_a, perspective_b],
            contradiction_count=1,
            severity=severity,  # type: ignore
        )

        self._contradictions[domain].append(report)
        self.logger.info(
            f"Recorded contradiction in {domain}: {perspective_a} vs {perspective_b} "
            f"(severity: {severity})"
        )

    def get_statistics(self) -> dict:
        """Get engine statistics."""
        # Clean old perspectives
        self._cleanup_old_perspectives()

        domain_stats = []
        for domain, perspectives in self._perspectives.items():
            total_claims = sum(p.claim_count for p in perspectives.values())
            domain_stats.append({
                "domain": domain,
                "perspectiveCount": len(perspectives),
                "totalClaims": total_claims,
                "perspectives": [
                    {
                        "perspectiveId": p.perspective_id,
                        "claimCount": p.claim_count,
                        "avgConfidence": p.avg_confidence,
                    }
                    for p in sorted(
                        perspectives.values(),
                        key=lambda x: x.claim_count,
                        reverse=True
                    )
                ],
            })

        return {
            "totalAnalyzed": self._total_analyzed,
            "totalWarnings": self._total_warnings,
            "totalThrottled": self._total_throttled,
            "domains": domain_stats,
        }

    def _cleanup_old_perspectives(self) -> None:
        """Remove perspectives outside the analysis window."""
        cutoff = datetime.utcnow() - timedelta(hours=self.config.analysis_window_hours)

        for domain in list(self._perspectives.keys()):
            perspectives_to_remove = [
                pid
                for pid, p in self._perspectives[domain].items()
                if p.latest_seen and p.latest_seen < cutoff
            ]

            for pid in perspectives_to_remove:
                del self._perspectives[domain][pid]
                self.logger.debug(f"Cleaned up old perspective: {domain}/{pid}")

            # Remove empty domains
            if not self._perspectives[domain]:
                del self._perspectives[domain]

    def get_domain_diversity_report(self, domain: str) -> dict:
        """
        Get a detailed diversity report for a specific domain.

        Args:
            domain: Topic domain

        Returns:
            Detailed diversity report
        """
        if domain not in self._perspectives:
            return {
                "domain": domain,
                "error": "Domain not found",
            }

        perspectives = self._perspectives[domain]
        assessment = self._assess_plurality(domain, "")

        return {
            "domain": domain,
            "assessment": assessment.plurality_level,
            "metrics": {
                "perspectiveCount": assessment.metrics.perspective_count,
                "shannonDiversity": assessment.metrics.shannon_diversity,
                "dominantShare": assessment.metrics.dominant_perspective_share,
                "minorityCount": assessment.metrics.minority_perspective_count,
            },
            "perspectives": [
                {
                    "perspectiveId": p.perspective_id,
                    "claimCount": p.claim_count,
                    "avgConfidence": p.avg_confidence,
                    "sources": p.source_distribution,
                    "stanceSummary": p.stance_summary,
                }
                for p in sorted(
                    perspectives.values(),
                    key=lambda x: x.claim_count,
                    reverse=True
                )
            ],
            "contradictions": [
                {
                    "conflictingPerspectives": c.conflicting_perspectives,
                    "severity": c.severity,
                }
                for c in self._contradictions.get(domain, [])
            ],
            "recommendations": assessment.recommendations,
        }


def create_plurality_preservation_rules(
    config: PluralityPreservationConfig | None = None,
) -> PluralityPreservationRules:
    """
    Factory function to create a PluralityPreservationRules instance.

    Args:
        config: Engine configuration

    Returns:
        Configured PluralityPreservationRules instance
    """
    return PluralityPreservationRules(config=config)
