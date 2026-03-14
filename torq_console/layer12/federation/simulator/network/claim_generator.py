"""
Calibrated Claim Generator for Network Simulation

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Generates claims with calibrated quality to achieve target acceptance rates.
This is critical for signal-rich network behavior simulation.

Key concepts:
- Claim quality bias affects eligibility scores and acceptance
- Different scenarios require different quality levels
- Calibration ensures meaningful simulation results
"""

import logging
import random
from datetime import datetime
from typing import Optional

import numpy as np

from ..models import Domain, NodeBehaviorProfile, SimulatedClaim, Stance
from .node_registry import SimulatedNetworkNode


logger = logging.getLogger(__name__)


class CalibratedClaimGenerator:
    """
    Generates claims with calibrated quality for realistic acceptance rates.

    Acceptance rate is primarily driven by the eligibility filter,
    which depends on:
    1. Confidence score (threshold ~0.3-0.5)
    2. Provenance quality (threshold ~0.5)
    3. Overall score (threshold ~0.5)

    By controlling these parameters, we can achieve target acceptance rates.
    """

    # Calibration targets (based on Phase 2A validation)
    # These produce ~20-40% acceptance in simulation mode

    def __init__(self, quality_bias: float = 0.75):
        """
        Initialize the claim generator.

        Args:
            quality_bias: Overall claim quality (0.5-0.95)
                - 0.50: Very low quality (~0-5% acceptance)
                - 0.60: Low quality (~5-15% acceptance)
                - 0.70: Medium-low quality (~15-30% acceptance)
                - 0.75: Medium quality (~25-45% acceptance) - RECOMMENDED BASELINE
                - 0.80: High quality (~40-60% acceptance)
                - 0.90: Very high quality (~60-80% acceptance)
        """
        self.quality_bias = quality_bias
        self.logger = logging.getLogger(__name__)

    def generate_claim(
        self,
        node: SimulatedNetworkNode,
        epoch: int,
        domain: Optional[Domain] = None,
        stance: Optional[Stance] = None,
    ) -> SimulatedClaim:
        """
        Generate a calibrated claim from a node.

        Args:
            node: The node generating the claim
            epoch: Current simulation epoch
            domain: Optional domain override
            stance: Optional stance override

        Returns:
            Calibrated SimulatedClaim
        """
        # Determine domain
        if domain is None:
            domain = node.domain_specializations[0] if node.domain_specializations else Domain.GENERAL

        # Determine stance (with some bias from node's behavior)
        if stance is None:
            stance = self._select_stance(node)

        # Generate calibrated confidence and provenance
        confidence = self._generate_confidence(node)
        provenance_quality = self._generate_provenance_quality(node)

        # Generate content
        content = self._generate_claim_content(node, domain, stance)

        claim = SimulatedClaim(
            claim_id=f"{node.node_id}_epoch{epoch}_{random.randint(1000, 9999)}",
            source_node_id=node.node_id,
            content=content,
            domain=domain,
            stance=stance,
            confidence=confidence,
            provenance_quality=provenance_quality,
            timestamp=datetime.utcnow(),
        )

        self.logger.debug(
            f"Generated claim {claim.claim_id}: "
            f"confidence={confidence:.2f}, provenance={provenance_quality:.2f}"
        )

        return claim

    def _select_stance(self, node: SimulatedNetworkNode) -> Stance:
        """Select stance based on node's behavior profile."""
        if hasattr(node.behavior_profile, 'stance_bias'):
            # Use stance_bias distribution if available
            biases = node.behavior_profile.stance_bias
            stances = list(biases.keys())
            weights = list(biases.values())
            return random.choices(stances, weights=weights, k=1)[0]
        else:
            # Default distribution
            return random.choice(list(Stance))

    def _generate_confidence(self, node: SimulatedNetworkNode) -> float:
        """
        Generate calibrated confidence score.

        Target: ~0.5-0.95 for 20-40% acceptance
        - Must be >= 0.3 to pass basic confidence check
        - Should be 0.5-0.8 for realistic acceptance
        """
        # Base range from behavior profile
        if hasattr(node.behavior_profile, 'confidence_range'):
            min_conf, max_conf = node.behavior_profile.confidence_range
        else:
            min_conf, max_conf = 0.5, 0.95

        # Adjust by quality_bias
        # Shift the range up or down based on quality_bias
        range_mid = (min_conf + max_conf) / 2
        range_width = (max_conf - min_conf) / 2

        # Apply quality bias adjustment
        adjustment = (self.quality_bias - 0.75) * 0.3  # +/- adjustment
        new_mid = max(0.4, min(0.9, range_mid + adjustment))

        # Generate within adjusted range
        confidence = random.uniform(
            max(0.3, new_mid - range_width),
            min(0.95, new_mid + range_width)
        )

        return float(confidence)

    def _generate_provenance_quality(self, node: SimulatedNetworkNode) -> float:
        """
        Generate calibrated provenance quality.

        Target: ~0.6-0.9 for 20-40% acceptance
        - Must be >= 0.5 to pass eligibility filter
        - Higher quality = better acceptance
        """
        # Base from behavior profile
        if hasattr(node.behavior_profile, 'provenance_quality'):
            base_quality = node.behavior_profile.provenance_quality
        else:
            base_quality = 0.7

        # Adjust by quality_bias
        # Shift provenance up/down based on quality_bias
        adjustment = (self.quality_bias - 0.75) * 0.2
        provenance_quality = max(0.5, min(0.95, base_quality + adjustment))

        # Add some noise
        noise = random.uniform(-0.05, 0.05)
        provenance_quality = max(0.5, min(0.95, provenance_quality + noise))

        return float(provenance_quality)

    def _generate_claim_content(
        self,
        node: SimulatedNetworkNode,
        domain: Domain,
        stance: Stance,
    ) -> str:
        """Generate claim content based on domain and stance."""
        templates = {
            Domain.TECHNICAL: [
                "Proposed optimization for {subsystem} could improve efficiency by {amount}%.",
                "Analysis of {technology} integration reveals potential gains in {metric}.",
                "Refactoring {component} would enhance maintainability and reduce {risk}.",
                "Benchmark shows {system} performance is {assessment} for {workload}.",
            ],
            Domain.STRATEGIC: [
                "Market analysis suggests {opportunity} in {sector} over next {timeframe}.",
                "Competitive positioning indicates {advantage} relative to {competitor}.",
                "Strategic initiative for {initiative} shows projected ROI of {roi}%.",
                "Risk assessment for {project} indicates {level} exposure to {risk_type}.",
            ],
            Domain.OPERATIONAL: [
                "Process optimization in {area} reduced cycle time by {amount}%.",
                "Resource allocation for {resource} shows {efficiency} utilization.",
                "Operational metric {metric} is {trend} following {change}.",
                "Workflow analysis for {process} reveals {opportunity} for improvement.",
            ],
            Domain.FINANCIAL: [
                "Financial analysis of {investment} shows {return} return potential.",
                "Budget allocation for {category} indicates {trend} spending pattern.",
                "Revenue projection for {segment} is {growth} over {period}.",
                "Cost optimization in {area} could save {amount} annually.",
            ],
            Domain.SECURITY: [
                "Security audit identified {vulnerability} in {component} with {severity} impact.",
                "Penetration testing revealed {issue} in {module} requiring {mitigation}.",
                "Threat modeling recommends {control} for {attack_vector} risk reduction.",
                "Compliance assessment for {regulation} shows {status} posture.",
            ],
            Domain.PERFORMANCE: [
                "Benchmarking shows {metric} is within {range} range for {context}.",
                "Optimization of {process} improved throughput by {amount}%.",
                "Load testing indicates {system} handles {load} with {latency} latency.",
                "Performance profiling identified {bottleneck} as primary constraint.",
            ],
            Domain.SCALABILITY: [
                "Scalability analysis shows {system} can handle {growth} growth.",
                "Architecture review recommends {pattern} for {scale} scale requirements.",
                "Capacity planning for {service} indicates {headroom} headroom.",
                "Auto-scaling configuration for {resource} optimized for {traffic_pattern}.",
            ],
            Domain.GENERAL: [
                "Analysis of {topic} suggests {conclusion} with {confidence} confidence.",
                "Review of {subject} indicates {finding} for {context}.",
                "Investigation into {area} revealed {result} requiring {action}.",
                "Assessment of {initiative} shows {outcome} for {stakeholder}.",
            ],
        }

        domain_templates = templates.get(domain, templates[Domain.GENERAL])
        template = random.choice(domain_templates)

        # Fill in placeholders with realistic values
        placeholders = {
            "{subsystem}": random.choice(["cache layer", "database", "API gateway", "message queue", "storage system"]),
            "{technology}": random.choice(["Redis", "PostgreSQL", "GraphQL", "Kafka", "RabbitMQ", "Elasticsearch"]),
            "{component}": random.choice(["auth module", "data layer", "UI", "middleware", "service mesh"]),
            "{amount}": f"{random.randint(5, 50)}",
            "{metric}": random.choice(["latency", "throughput", "error rate", "utilization", "response time"]),
            "{system}": random.choice(["API", "database", "cache", "worker", "gateway"]),
            "{assessment}": random.choice(["acceptable", "good", "excellent", "suboptimal", "optimal"]),
            "{workload}": random.choice(["read-heavy", "write-heavy", "mixed", "burst", "steady"]),
            "{opportunity}": random.choice(["growth", "expansion", "consolidation", "diversification"]),
            "{sector}": random.choice(["enterprise", "SMB", "consumer", "government"]),
            "{timeframe}": random.choice(["Q1", "Q2", "H1", "H2", "next year", "next quarter"]),
            "{advantage}": random.choice(["significant", "moderate", "slight", "competitive"]),
            "{competitor}": random.choice(["market leader", "emerging player", "incumbent", "disruptor"]),
            "{initiative}": random.choice(["digital transformation", "cloud migration", "AI adoption", "automation"]),
            "{roi}": f"{random.randint(10, 300)}",
            "{project}": random.choice(["platform upgrade", "security hardening", "performance tuning", "cost optimization"]),
            "{level}": random.choice(["low", "moderate", "elevated", "high"]),
            "{risk_type}": random.choice(["technical", "operational", "financial", "regulatory"]),
            "{area}": random.choice(["deployment", "monitoring", "testing", "documentation"]),
            "{resource}": random.choice(["compute", "storage", "network", "memory"]),
            "{efficiency}": random.choice(["high", "improved", "optimal", "efficient"]),
            "{investment}": random.choice(["cloud infrastructure", "R&D", "acquisition", "product launch"]),
            "{return}": random.choice(["positive", "strong", "moderate", "attractive"]),
            "{category}": random.choice(["engineering", "marketing", "sales", "operations"]),
            "{trend}": random.choice(["increasing", "stable", "decreasing", "volatile"]),
            "{segment}": random.choice(["enterprise", "SMB", "consumer", "government"]),
            "{growth}": random.choice(["15%", "25%", "40%", "50%"]),
            "{period}": random.choice(["Q1", "H1", "FY", "next quarter"]),
            "{vulnerability}": random.choice(["XSS", "SQL injection", "CSRF", "authentication bypass"]),
            "{severity}": random.choice(["high", "critical", "moderate", "low"]),
            "{issue}": random.choice(["injection flaw", "misconfiguration", "weak encryption", "exposed endpoint"]),
            "{mitigation}": random.choice(["input validation", "WAF", "encryption", "access controls"]),
            "{control}": random.choice(["monitoring", "rate limiting", "authentication", "authorization"]),
            "{attack_vector}": random.choice(["injection", "XSS", "brute force", "DoS"]),
            "{range}": random.choice(["acceptable", "expected", "target", "optimal"]),
            "{context}": random.choice(["production", "peak load", "normal operation", "stress test"]),
            "{process}": random.choice(["data pipeline", "API", "batch job", "workflow"]),
            "{load}": random.choice(["10K RPS", "100K RPS", "1M RPS", "concurrent users"]),
            "{latency}": random.choice(["<50ms", "<100ms", "<200ms", "sub-second"]),
            "{bottleneck}": random.choice(["database", "network", "CPU", "I/O"]),
            "{growth}": random.choice(["2x", "3x", "5x", "10x"]),
            "{pattern}": random.choice(["microservices", "event-driven", "CQRS", "sharding"]),
            "{scale}": random.choice(["horizontal", "vertical", "distributed"]),
            "{service}": random.choice(["API", "worker", "database", "cache"]),
            "{headroom}": random.choice(["2x", "3x", "50%", "100%"]),
            "{resource}": random.choice(["containers", "instances", "connections", "requests"]),
            "{traffic_pattern}": random.choice(["diurnal", "spiky", "steady", "growing"]),
            "{topic}": random.choice(["market trend", "technology shift", "customer need", "competitive move"]),
            "{conclusion}": random.choice(["opportunity", "risk", "stable outlook", "caution"]),
            "{confidence}": random.choice(["high", "moderate", "low"]),
            "{subject}": random.choice(["product", "strategy", "process", "technology"]),
            "{finding}": random.choice(["strength", "weakness", "opportunity", "threat"]),
            "{area}": random.choice(["architecture", "operations", "security", "performance"]),
            "{result}": random.choice(["efficiency gain", "cost saving", "risk reduction", "quality improvement"]),
            "{action}": random.choice(["immediate action", "monitoring", "investigation", "optimization"]),
            "{initiative}": random.choice(["modernization", "optimization", "expansion", "consolidation"]),
            "{outcome}": random.choice(["success", "mixed results", "challenges", "opportunities"]),
            "{stakeholder}": random.choice(["customers", "investors", "employees", "partners"]),
        }

        result = template
        for placeholder, value in placeholders.items():
            result = result.replace(placeholder, value)

        return result


def create_claim_generator(quality_bias: float = 0.75) -> CalibratedClaimGenerator:
    """Factory function to create a CalibratedClaimGenerator."""
    return CalibratedClaimGenerator(quality_bias=quality_bias)
