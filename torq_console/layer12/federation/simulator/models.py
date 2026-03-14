"""
Federation Simulator Models

Layer 12 Phase 2A — Federation Stability Validation Harness

Core simulation data models for the 3-5 node federation simulator.
"""

import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class NodeType(Enum):
    """Types of simulated nodes."""
    NORMAL = "normal"
    AGGRESSIVE = "aggressive"
    CAUTIOUS = "cautious"
    EXPERT = "expert"
    ADVERSARIAL = "adversarial"


class Stance(Enum):
    """Claim stances/perspectives."""
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    CONDITIONAL = "conditional"
    MIXED = "mixed"


class QualityLevel(Enum):
    """Claim quality levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPAM = "spam"


class Domain(Enum):
    """Knowledge domains."""
    TECHNICAL = "technical"
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SCALABILITY = "scalability"
    GENERAL = "general"


# ============================================================================
# Node Models
# ============================================================================

@dataclass
class NodeBehaviorProfile:
    """Behavioral characteristics of a simulated node."""

    # Base characteristics
    node_type: NodeType = NodeType.NORMAL
    baseline_trust: float = 0.7
    domains: List[Domain] = field(default_factory=lambda: [Domain.GENERAL])

    # Claim generation
    base_claim_rate: float = 1.0  # claims per round
    stance_bias: Dict[Stance, float] = field(
        default_factory=lambda: {
            Stance.SUPPORT: 0.35,
            Stance.OPPOSE: 0.25,
            Stance.NEUTRAL: 0.2,
            Stance.CONDITIONAL: 0.15,
            Stance.MIXED: 0.05,
        }
    )

    # Quality profile - Calibrated for 20-40% baseline acceptance
    quality_level: QualityLevel = QualityLevel.MEDIUM

    # Confidence range: adjusted for realistic acceptance rates
    # For baseline healthy exchange, use 0.5-0.95 to ensure some pass eligibility
    # Values below 0.3 will fail the confidence check
    # Values between 0.3-0.5 may pass confidence but struggle with overall score
    confidence_range: Tuple[float, float] = (0.5, 0.95)

    # Provenance quality: must be >= 0.5 to pass eligibility filter
    # Set to 0.6-0.85 for baseline to ensure good acceptance rate
    provenance_quality: float = 0.7

    # Adversarial settings
    is_adversarial: bool = False
    adversarial_mode: Optional[str] = None  # "flood", "monoculture", "trust_gaming", etc.

    # Trust behavior
    trust_stability: float = 0.9  # How stable trust remains over time
    trust_volatility: float = 0.1  # Natural fluctuation

    def __post_init__(self):
        """Validate behavioral profile."""
        if sum(self.stance_bias.values()) != 1.0:
            raise ValueError("Stance bias probabilities must sum to 1.0")

        if not 0.0 <= self.baseline_trust <= 1.0:
            raise ValueError("Baseline trust must be between 0.0 and 1.0")


@dataclass
class NodeState:
    """Current state of a simulated node."""

    node_id: str
    profile: NodeBehaviorProfile

    # Dynamic state
    current_trust: float = 0.5  # Default trust if not specified
    total_submissions: int = 0
    accepted_submissions: int = 0
    rejected_submissions: int = 0

    # Recent claims (for tracking)
    recent_claims: List[str] = field(default_factory=list)
    claim_timestamps: List[datetime] = field(default_factory=list)

    # Trust history
    trust_observations: List[float] = field(default_factory=list)
    trust_timestamps: List[datetime] = field(default_factory=list)

    # Performance tracking
    average_trust_score: float = 0.0
    quality_score_avg: float = 0.0

    # Domain leadership
    domain_leadership: Dict[Domain, int] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize with baseline trust."""
        self.current_trust = self.profile.baseline_trust


class SimulatedNode:
    """A simulated TORQ federation node."""

    def __init__(
        self,
        node_id: str,
        profile: NodeBehaviorProfile,
        state: Optional[NodeState] = None,
    ):
        self.node_id = node_id
        self.profile = profile
        # Use provided state or create new one with baseline trust
        self.state = state or NodeState(
            node_id=node_id,
            profile=profile,
            current_trust=profile.baseline_trust
        )

        # Statistics
        self.total_generated = 0
        self.total_accepted = 0
        self.total_rejected = 0

    def generate_claim(self, round_num: int, available_domains: List[Domain]) -> "SimulatedClaim":
        """Generate a claim based on node profile and current state.

        Calibrated for 20-40% acceptance rate in baseline scenarios by ensuring:
        - Confidence in range that passes eligibility filter (>= 0.3)
        - Provenance quality >= 0.5 (eligibility requirement)
        - Content length within bounds (20-5000 chars)
        """

        # Select domain
        if self.profile.adversarial_mode == "monoculture":
            # Force same domain for monoculture attack
            domain = self.profile.domains[0] if self.profile.domains else Domain.GENERAL
        else:
            # Select domain based on profile or weighted random
            domain = random.choice(available_domains)

        # Select stance
        stance = random.choices(
            list(Stance),
            weights=[self.profile.stance_bias[s] for s in Stance],
            k=1
        )[0]

        # Generate confidence based on node type and quality profile
        # Calibrated for 20-40% acceptance rate
        if self.profile.node_type == NodeType.EXPERT:
            # Expert nodes: high confidence (mostly pass eligibility)
            confidence = random.uniform(0.75, 0.95)
        elif self.profile.node_type == NodeType.CAUTIOUS:
            # Cautious nodes: good confidence with some variation
            confidence = random.uniform(0.65, 0.9)
        elif self.profile.node_type == NodeType.NORMAL:
            # Normal nodes: medium confidence (mixed pass/fail)
            confidence = random.uniform(0.5, 0.85)
        elif self.profile.node_type == NodeType.AGGRESSIVE:
            # Aggressive nodes: wider range
            confidence = random.uniform(0.4, 0.8)
        else:  # ADVERSARIAL
            # Adversarial nodes: lower confidence (mostly fail)
            confidence = random.uniform(0.2, 0.5)

        # Generate provenance quality based on node type
        # Must be >= 0.5 to pass eligibility filter's provenance check
        if self.profile.node_type == NodeType.EXPERT:
            provenance_quality = random.uniform(0.8, 0.95)
        elif self.profile.node_type == NodeType.CAUTIOUS:
            provenance_quality = random.uniform(0.7, 0.9)
        elif self.profile.node_type == NodeType.NORMAL:
            provenance_quality = random.uniform(0.6, 0.85)
        elif self.profile.node_type == NodeType.AGGRESSIVE:
            provenance_quality = random.uniform(0.5, 0.75)
        else:  # ADVERSARIAL
            # Adversarial: low provenance (mostly fail)
            provenance_quality = random.uniform(0.2, 0.5)

        # Generate content based on domain and stance
        content = self._generate_content(domain, stance)

        # Create claim
        claim = SimulatedClaim(
            claim_id=f"{self.node_id}_round{round_num}_{self.total_generated}",
            source_node_id=self.node_id,
            domain=domain,
            stance=stance,
            confidence=confidence,
            provenance_quality=provenance_quality,
            content=content,
            timestamp=datetime.utcnow(),
        )

        # Update node statistics
        self.total_generated += 1
        self.state.total_submissions += 1
        self.state.recent_claims.append(claim.claim_id)
        self.state.claim_timestamps.append(claim.timestamp)

        # Clean old claims (keep last 50)
        if len(self.state.recent_claims) > 50:
            self.state.recent_claims.pop(0)
            self.state.claim_timestamps.pop(0)

        return claim

    def _generate_content(self, domain: Domain, stance: Stance) -> str:
        """Generate realistic content based on domain and stance.

        Content length is calibrated to be within eligibility bounds (20-5000 chars).
        Typical generated content is 80-150 characters.
        """

        domain_templates = {
            Domain.TECHNICAL: [
                "The current implementation shows significant potential for improvement in {topic}.",
                "Analysis of {topic} reveals several critical considerations that must be addressed.",
                "Our approach to {topic} has been effective but there are optimization opportunities.",
                "The technical details of {topic} require careful examination and refinement.",
            ],
            Domain.STRATEGIC: [
                "Strategic positioning regarding {topic} should be reconsidered given market conditions.",
                "Long-term strategy must account for the implications of {topic} on our objectives.",
                "The strategic implications of {topic} warrant careful analysis and planning.",
                "Our approach to {topic} aligns with core strategic priorities.",
            ],
            Domain.OPERATIONAL: [
                "Operational efficiency in {topic} can be significantly improved with process adjustments.",
                "Current operational practices around {topic} require standardization and optimization.",
                "The operational impact of {topic} needs to be carefully monitored and managed.",
                "We've seen good operational results from implementing {topic}.",
            ],
            Domain.FINANCIAL: [
                "Financial considerations for {topic} show promising returns with appropriate risk management.",
                "The cost-benefit analysis of {topic} indicates favorable long-term prospects.",
                "Financial implications of {topic} require careful modeling and forecasting.",
                "Investment in {topic} has demonstrated strong financial returns.",
            ],
            Domain.SECURITY: [
                "Security posture around {topic} needs strengthening to address emerging threats.",
                "Current security measures for {topic} provide adequate protection but gaps exist.",
                "Security considerations for {topic} must be prioritized in our risk framework.",
                "We've implemented robust security protocols for {topic}.",
            ],
            Domain.PERFORMANCE: [
                "Performance metrics for {topic} show consistent improvement over time.",
                "Optimization opportunities exist in {topic} that could enhance system performance.",
                "Performance monitoring of {topic} indicates stable operation.",
                "The performance characteristics of {topic} are within acceptable parameters.",
            ],
            Domain.SCALABILITY: [
                "Scalability concerns for {topic} require architectural attention.",
                "Current approaches to {topic} demonstrate good scalability characteristics.",
                "The scalability implications of {topic} need to be evaluated carefully.",
                "Our implementation of {topic} scales effectively under load.",
            ],
            Domain.GENERAL: [
                "The discussion around {topic} has provided valuable insights.",
                "Further consideration of {topic} is warranted to ensure comprehensive coverage.",
                "The implications of {topic} affect multiple areas of our operations.",
                "We continue to monitor developments in {topic} closely.",
            ],
        }

        stance_modifiers = {
            Stance.SUPPORT: [
                "strongly recommend",
                "fully endorse",
                "support the initiative",
                "advocate for",
                "believe in the value of",
            ],
            Stance.OPPOSE: [
                "caution against",
                "recommend against",
                "express concerns about",
                "oppose the current approach",
                "question the viability of",
            ],
            Stance.NEUTRAL: [
                "acknowledge",
                "recognize",
                "note the importance of",
                "understand the relevance of",
                "consider",
            ],
            Stance.CONDITIONAL: [
                "support with proper safeguards",
                "endorse subject to review",
                "recommend contingent on",
                "support if implemented with",
                "endorse provided that",
            ],
            Stance.MIXED: [
                "recognize both benefits and challenges",
                "see advantages but also concerns",
                "support aspects while questioning others",
                "endorne partially with reservations",
                "support in principle but require details",
            ],
        }

        # Get templates for domain and stance
        domain_content = domain_templates.get(domain, domain_templates[Domain.GENERAL])
        stance_content = stance_modifiers.get(stance, stance_modifiers[Stance.NEUTRAL])

        # Generate topic based on domain
        topics = {
            Domain.TECHNICAL: ["API design", "database optimization", "caching strategies", "load balancing"],
            Domain.STRATEGIC: ["market positioning", "competitive analysis", "growth strategy", "innovation roadmap"],
            Domain.OPERATIONAL: ["process improvement", "resource allocation", "workflow optimization", "team coordination"],
            Domain.FINANCIAL: ["budget planning", "cost optimization", "ROI analysis", "investment strategy"],
            Domain.SECURITY: ["access control", "vulnerability management", "compliance", "threat detection"],
            Domain.PERFORMANCE: ["latency optimization", "throughput improvement", "resource utilization", "response time"],
            Domain.SCALABILITY: ["horizontal scaling", "vertical scaling", "load testing", "capacity planning"],
            Domain.GENERAL: ["strategic alignment", "operational excellence", "risk management", "performance"],
        }

        topic = random.choice(topics.get(domain, ["strategic initiatives"]))
        stance_modifier = random.choice(stance_content)
        domain_template = random.choice(domain_content)

        # Generate final content (typically 80-150 characters, well within 20-5000 bounds)
        content = f"{stance_modifier.title()} {domain_template.format(topic=topic)}"

        return content


# ============================================================================
# Claim Models
# ============================================================================

class SimulatedClaim:
    """A simulated federated claim."""

    def __init__(
        self,
        claim_id: str,
        source_node_id: str,
        domain: Domain,
        stance: Stance,
        confidence: float,
        provenance_quality: float,
        content: str,
        timestamp: datetime,
        is_duplicate: bool = False,
        is_replay: bool = False,
    ):
        self.claim_id = claim_id
        self.source_node_id = source_node_id
        self.domain = domain
        self.stance = stance
        self.confidence = confidence
        self.provenance_quality = provenance_quality
        self.content = content
        self.timestamp = timestamp
        self.is_duplicate = is_duplicate
        self.is_replay = is_replay

        # Processing results
        self.processing_result: Optional[Any] = None
        self.trusted_after_processing: Optional[float] = None
        self.final_decision: Optional[str] = None

    def calculate_quality_score(self) -> float:
        """Calculate overall quality score for the claim."""
        return (
            self.confidence * 0.4 +
            self.provenance_quality * 0.6
        )

    def to_federated_payload(self) -> Dict[str, Any]:
        """Convert to format expected by federation pipeline."""
        return {
            "artifact_id": self.claim_id,
            "source_node_id": self.source_node_id,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "provenance_quality": self.provenance_quality,
            "domain": self.domain.value,
            "stance": self.stance.value,
            "content": self.content,
            "quality_score": self.calculate_quality_score(),
            "is_duplicate": self.is_duplicate,
            "is_replay": self.is_replay,
        }


# ============================================================================
# Simulation Models
# ============================================================================

@dataclass
class SimulationRound:
    """State for a single simulation round."""

    round_number: int
    nodes: List[SimulatedNode]
    claims: List[SimulatedClaim]
    round_start_time: datetime = field(default_factory=datetime.utcnow)
    execution_time: timedelta = field(default_factory=timedelta)

    # Processing results
    processed_claims: List[Any] = field(default_factory=list)  # Can be ProcessedSimulationClaimResult or SimulatedClaim
    rejected_claims: List[SimulatedClaim] = field(default_factory=list)
    accepted_claims: List[SimulatedClaim] = field(default_factory=list)

    # Metrics
    diversity_metrics: Dict[str, float] = field(default_factory=dict)
    concentration_metrics: Dict[str, float] = field(default_factory=dict)
    trust_metrics: Dict[str, float] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    resilience_metrics: Dict[str, float] = field(default_factory=dict)

    # Predictive metrics summary (optional, use forward reference)
    round_summary: Optional["RoundSummary"] = None

    def add_processed_claim(self, claim: SimulatedClaim, decision: str):
        """Add a processed claim to the round results."""
        self.processed_claims.append(claim)
        claim.final_decision = decision

        if decision == "accept":
            self.accepted_claims.append(claim)
        else:
            self.rejected_claims.append(claim)

    def get_total_acceptance_rate(self) -> float:
        """Calculate acceptance rate for the round."""
        if not self.processed_claims:
            return 0.0
        return len(self.accepted_claims) / len(self.processed_claims)


@dataclass
class SimulationScenario:
    """A stress-test scenario configuration."""

    name: str
    description: str = ""

    # Configuration
    num_nodes: int = 5
    rounds: int = 20
    domain_distribution: Dict[Domain, float] = field(
        default_factory=lambda: {
            Domain.TECHNICAL: 0.3,
            Domain.STRATEGIC: 0.2,
            Domain.OPERATIONAL: 0.2,
            Domain.FINANCIAL: 0.15,
            Domain.SECURITY: 0.15,
        }
    )

    # Node behavior configuration
    node_types: List[NodeType] = field(
        default_factory=lambda: [
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.CAUTIOUS,
            NodeType.EXPERT,
        ]
    )

    # Adversarial settings
    adversarial_nodes: List[str] = field(default_factory=list)
    adversarial_modes: Dict[str, str] = field(default_factory=dict)
    adversarial_intensity: float = 1.0

    # Expected outcomes
    expected_guardian_triggers: List[str] = field(default_factory=list)
    expected_outcomes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate scenario configuration."""
        if sum(self.domain_distribution.values()) != 1.0:
            raise ValueError("Domain distribution must sum to 1.0")

        if len(self.node_types) != self.num_nodes:
            raise ValueError("Number of node types must match num_nodes")


# ============================================================================
# Report Models
# ============================================================================

@dataclass
class SimulationMetrics:
    """Aggregated metrics for a simulation run."""

    # Overall health
    overall_health_index: float = 0.0

    # Category metrics
    diversity_health: float = 0.0
    influence_balance: float = 0.0
    trust_stability: float = 0.0
    quality_integrity: float = 0.0
    resilience: float = 0.0

    # Detailed metrics
    topic_entropy: float = 0.0
    stance_entropy: float = 0.0
    gini_coefficient: float = 0.0
    herfindahl_index: float = 0.0
    average_trust_drift: float = 0.0
    trust_volatility: float = 0.0
    acceptance_rate: float = 0.0
    rejection_rate: float = 0.0
    spam_detected_rate: float = 0.0
    duplicate_suppression_rate: float = 0.0

    # Node-level metrics
    node_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Round-by-round history
    round_history: List[Dict[str, Any]] = field(default_factory=list)

    # Predictive metrics
    eddr: float = 0.0  # Epistemic Diversity Decay Rate
    aca: float = 0.0  # Authority Capture Acceleration
    fcri: float = 0.0  # Federation Collapse Risk Index
    predictive_status: str = "healthy"  # Risk status from predictive metrics

    def calculate_federation_health_index(self) -> float:
        """Calculate overall federation health index."""
        weights = {
            "diversity_health": 0.25,
            "influence_balance": 0.20,
            "trust_stability": 0.20,
            "quality_integrity": 0.20,
            "resilience": 0.15,
        }

        self.overall_health_index = sum(
            getattr(self, category) * weight
            for category, weight in weights.items()
        )

        return self.overall_health_index


class SimulationReport:
    """Complete simulation report with results and analysis."""

    def __init__(
        self,
        scenario: SimulationScenario,
        metrics: SimulationMetrics,
        execution_time: timedelta,
        success_rate: float,
        eddr_result: Optional["EpistemicDiversityDecayResult"] = None,
        aca_result: Optional["AuthorityCaptureAccelerationResult"] = None,
        fcri_result: Optional["FederationCollapseRiskResult"] = None,
    ):
        self.scenario = scenario
        self.metrics = metrics
        self.execution_time = execution_time
        self.success_rate = success_rate

        # Predictive metrics
        self.eddr_result = eddr_result
        self.aca_result = aca_result
        self.fcri_result = fcri_result

        # Round results
        self.rounds: List[SimulationRound] = []

        # Analysis
        self.guardian_triggers_detected: Dict[str, int] = defaultdict(int)
        self.safeguard_effectiveness: Dict[str, float] = {}
        self.failure_points: List[str] = []
        self.recommendations: List[str] = []

    def add_guardian_trigger(self, guardian_name: str, count: int = 1):
        """Record a guardian safeguard trigger."""
        self.guardian_triggers_detected[guardian_name] += count

    def calculate_safeguard_effectiveness(self) -> Dict[str, float]:
        """Calculate effectiveness of each safeguard."""
        total_triggers = sum(self.guardian_triggers_detected.values())

        for guardian in [
            "FederationEligibilityFilter",
            "ContextSimilarityEngine",
            "PluralityPreservationRules",
            "AllocativeBoundaryGuard",
            "TrustDecayModel"
        ]:
            if total_triggers > 0:
                effectiveness = self.guardian_triggers_detected[guardian] / total_triggers
            else:
                effectiveness = 0.0
            self.safeguard_effectiveness[guardian] = effectiveness

        return self.safeguard_effectiveness

    def generate_summary(self) -> str:
        """Generate human-readable summary."""
        health_status = (
            "healthy" if self.metrics.overall_health_index >= 0.85 else
            "stable" if self.metrics.overall_health_index >= 0.70 else
            "degraded" if self.metrics.overall_health_index >= 0.50 else
            "failing"
        )

        summary = f"""
Simulation Summary: {self.scenario.name}
-------------------------------------------
Health Status: {health_status.upper()}
Overall Health Index: {self.metrics.overall_health_index:.2f}
Success Rate: {self.success_rate:.1%}
Execution Time: {self.execution_time}

Metrics by Category:
- Diversity: {self.metrics.diversity_health:.2f}
- Influence Balance: {self.metrics.influence_balance:.2f}
- Trust Stability: {self.metrics.trust_stability:.2f}
- Quality Integrity: {self.metrics.quality_integrity:.2f}
- Resilience: {self.metrics.resilience:.2f}

Safeguard Triggers:
{chr(10).join(f"  - {k}: {v}" for k, v in self.guardian_triggers_detected.items())}
"""

        # Add predictive metrics section if available
        if self.fcri_result:
            summary += f"""
Predictive Risk Metrics:
- EDDR: {self.eddr_result.eddr if self.eddr_result else 0:.4f}
- ACA: {self.aca_result.aca if self.aca_result else 0:.4f}
- FCRI: {self.fcri_result.fcri:.4f} ({self.fcri_result.status})
"""

        return summary


# ============================================================================
# Predictive Risk Models
# ============================================================================

class PredictiveRiskStatus(str):
    """Risk status levels for predictive metrics."""
    HEALTHY = "healthy"
    WATCH = "watch"
    DEGRADING = "degrading"
    COLLAPSE_RISK = "collapse_risk"


@dataclass
class EpistemicDiversityDecayResult:
    """Result of epistemic diversity decay rate calculation."""

    current_diversity_score: float
    window_size: int
    eddr: float  # Epistemic Diversity Decay Rate
    status: PredictiveRiskStatus
    topic_entropy: float = 0.0
    stance_entropy: float = 0.0
    minority_ratio: float = 0.0
    contradiction_retention: float = 0.0
    dominant_nodes: List[str] = field(default_factory=list)
    dominant_domains: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class AuthorityCaptureAccelerationResult:
    """Result of authority capture acceleration calculation."""

    current_concentration_score: float
    window_size: int
    aca: float  # Authority Capture Acceleration
    status: PredictiveRiskStatus
    gini: float = 0.0
    hhi: float = 0.0
    top_1_share: float = 0.0
    top_2_share: float = 0.0
    dominant_nodes: List[str] = field(default_factory=list)
    dominant_domains: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class FederationCollapseRiskResult:
    """Result of federation collapse risk assessment."""

    fcri: float  # Federation Collapse Risk Index
    status: PredictiveRiskStatus
    primary_driver: str  # "authority_capture", "diversity_decay", "combined", "none"
    eddr: float = 0.0
    aca: float = 0.0
    dominant_nodes: List[str] = field(default_factory=list)
    dominant_domains: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class RoundSummary:
    """Summary of a single simulation round for predictive metrics."""

    round_number: int
    timestamp: datetime
    topic_entropy: float
    stance_entropy: float
    minority_ratio: float
    contradiction_retention: float
    gini: float
    hhi: float
    top_1_share: float
    top_2_share: float
    accepted_count: int
    rejected_count: int
    diversity_score: float = 0.0
    concentration_score: float = 0.0
