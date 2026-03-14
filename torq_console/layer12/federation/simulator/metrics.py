"""
Federation Simulator Metrics

Layer 12 Phase 2A — Federation Stability Validation Harness

Metrics collectors for measuring federation health across 5 categories:
1. Diversity health (topic entropy, stance entropy, minority survival)
2. Influence balance (Gini, HHI, concentration)
3. Trust stability (drift, volatility, anomalies)
4. Quality integrity (rejection rates, spam detection)
5. Resilience (throughput, recovery)
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

from .models import (
    Domain,
    SimulatedClaim,
    SimulatedNode,
    SimulationRound,
    SimulationMetrics,
    Stance,
    # Predictive risk models
    PredictiveRiskStatus,
    EpistemicDiversityDecayResult,
    AuthorityCaptureAccelerationResult,
    FederationCollapseRiskResult,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Claim Unwrapping Helper
# ============================================================================

def unwrap_claim(item: Any) -> SimulatedClaim:
    """
    Unwrap a claim from either SimulatedClaim or ProcessedSimulationClaimResult.

    The async executor wraps claims in ProcessedSimulationClaimResult.
    This helper extracts the original SimulatedClaim for metrics calculation.

    Args:
        item: Either a SimulatedClaim or ProcessedSimulationClaimResult

    Returns:
        The original SimulatedClaim
    """
    if hasattr(item, 'claim') and isinstance(item.claim, SimulatedClaim):
        return item.claim
    return item


def unwrap_claims(items: List[Any]) -> List[SimulatedClaim]:
    """
    Unwrap a list of claims from either SimulatedClaim or ProcessedSimulationClaimResult.

    Args:
        items: List of SimulatedClaim or ProcessedSimulationClaimResult

    Returns:
        List of SimulatedClaim objects
    """
    return [unwrap_claim(item) for item in items]


# ============================================================================
# Base Metric Calculator
# ============================================================================

class MetricCalculator:
    """Base class for metric calculators."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate the metric. Override in subclasses."""
        raise NotImplementedError

    def validate_range(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Validate metric value is within expected range."""
        return max(min_val, min(max_val, value))


# ============================================================================
# 1. Diversity Health Metrics
# ============================================================================

class TopicEntropyCalculator(MetricCalculator):
    """Calculate topic diversity using Shannon entropy."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate topic entropy for accepted claims."""
        rounds = simulation_data["rounds"]
        domain_claims = defaultdict(int)
        total_claims = 0

        for round_data in rounds:
            for claim in round_data.get("accepted_claims", []):
                domain_claims[claim.domain] += 1
                total_claims += 1

        if total_claims == 0:
            return 0.0

        # Calculate Shannon entropy
        entropy = 0.0
        for count in domain_claims.values():
            if count > 0:
                p = count / total_claims
                entropy -= p * math.log2(p)

        # Normalize to 0-1 range (max log2(8) = 3 for 8 domains)
        max_entropy = math.log2(8) if domain_claims else 1.0
        return self.validate_range(entropy / max_entropy)


class StanceEntropyCalculator(MetricCalculator):
    """Calculate stance diversity using Shannon entropy."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate stance entropy for accepted claims."""
        rounds = simulation_data["rounds"]
        stance_claims = defaultdict(int)
        total_claims = 0

        for round_data in rounds:
            for claim in round_data.get("accepted_claims", []):
                stance_claims[claim.stance] += 1
                total_claims += 1

        if total_claims == 0:
            return 0.0

        # Calculate Shannon entropy
        entropy = 0.0
        for count in stance_claims.values():
            if count > 0:
                p = count / total_claims
                entropy -= p * math.log2(p)

        # Normalize to 0-1 range (max log2(5) = 2.32 for 5 stances)
        max_entropy = math.log2(5) if stance_claims else 1.0
        return self.validate_range(entropy / max_entropy)


class MinorityViewpointSurvivalCalculator(MetricCalculator):
    """Calculate minority viewpoint survival rate."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate if minority viewpoints are preserved."""
        rounds = simulation_data["rounds"]
        domain_minority_threshold = 0.15  # 15% threshold for minority

        # Track stance distribution by domain
        domain_stance_dist = defaultdict(lambda: defaultdict(int))
        total_domain_claims = defaultdict(int)

        for round_data in rounds:
            for claim in round_data.get("accepted_claims", []):
                domain_stance_dist[claim.domain][claim.stance] += 1
                total_domain_claims[claim.domain] += 1

        # Calculate minority survival
        minority_survival_count = 0
        total_domains = 0

        for domain, stance_counts in domain_stance_dist.items():
            if total_domain_claims[domain] > 0:
                total_domains += 1

                # Find minority stances (those below threshold)
                total_in_domain = total_domain_claims[domain]
                minority_stances = [
                    stance for stance, count in stance_counts.items()
                    if count / total_in_domain < domain_minority_threshold
                ]

                # Minority survives if any minority stance has at least 1 claim
                minority_survival_count += len([
                    s for s in minority_stances
                    if stance_counts[s] >= 1
                ])

        if total_domains == 0:
            return 0.0

        # Return ratio of domains with preserved minority viewpoints
        return self.validate_range(minority_survival_count / total_domains)


class ContradictionRetentionCalculator(MetricCalculator):
    """Calculate healthy contradiction retention rate."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate rate of legitimate contradictions in accepted claims."""
        rounds = simulation_data["rounds"]
        contradiction_claims = 0
        total_claims = 0

        # Define contradictory stance pairs
        contradiction_pairs = [
            (Stance.SUPPORT, Stance.OPPOSE),
            (Stance.SUPPORT, Stance.CONDITIONAL),
            (Stance.OPPOSE, Stance.CONDITIONAL),
        ]

        for round_data in rounds:
            for claim in round_data.get("accepted_claims", []):
                total_claims += 1

                # Find contradictory claims in same domain
                for other_claim in round_data.get("accepted_claims", []):
                    if (claim.domain == other_claim.domain and
                        claim.claim_id != other_claim.claim_id):

                        # Check if stances are contradictory
                        stance_pair = (claim.stance, other_claim.stance)
                        reverse_pair = (other_claim.stance, claim.stance)

                        if stance_pair in contradiction_pairs or reverse_pair in contradiction_pairs:
                            contradiction_claims += 1
                            break

        if total_claims == 0:
            return 0.0

        # Return contradiction rate
        return self.validate_range(contradiction_claims / total_claims)


class DiversityHealthCalculator(MetricCalculator):
    """Calculate overall diversity health index."""

    def __init__(self):
        super().__init__("diversity_health")
        self.sub_calculators = [
            TopicEntropyCalculator("topic_entropy"),
            StanceEntropyCalculator("stance_entropy"),
            MinorityViewpointSurvivalCalculator("minority_survival"),
            ContradictionRetentionCalculator("contradiction_retention"),
        ]

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate weighted diversity health score."""
        scores = []
        details = {}

        for calculator in self.sub_calculators:
            score = calculator.calculate(simulation_data)
            scores.append(score)
            details[calculator.name] = score

        # Weighted average
        weights = [0.3, 0.3, 0.25, 0.15]  # Topic, stance, minority, contradiction
        diversity_score = sum(s * w for s, w in zip(scores, weights))

        # Store details for reporting
        simulation_data["diversity_details"] = details

        return self.validate_range(diversity_score)


# ============================================================================
# 2. Influence Balance Metrics
# ============================================================================

class GiniCoefficientCalculator(MetricCalculator):
    """Calculate Gini coefficient for influence concentration."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate Gini coefficient of node influence."""
        rounds = simulation_data["rounds"]
        node_influence = defaultdict(int)
        total_influence = 0

        # Calculate influence from accepted claims
        for round_data in rounds:
            for claim in round_data.get("accepted_claims", []):
                node_influence[claim.source_node_id] += 1
                total_influence += 1

        if total_influence == 0:
            return 0.0

        # Calculate Gini coefficient
        sorted_influences = sorted(node_influence.values())
        n = len(sorted_influences)

        if n == 1:
            return 0.0

        cum_sum = 0
        for i, influence in enumerate(sorted_influences):
            cum_sum += influence
            gini = (2 * (i + 1) - n - 1) * influence
            gini /= n * total_influence

        gini = abs(gini) * n / (n - 1)
        return self.validate_range(gini)


class HerfindahlIndexCalculator(MetricCalculator):
    """Calculate Herfindahl-Hirschman Index for concentration."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate HHI for node influence."""
        rounds = simulation_data["rounds"]
        node_influence = defaultdict(int)
        total_influence = 0

        # Calculate influence from accepted claims
        for round_data in rounds:
            for claim in round_data.get("accepted_claims", []):
                node_influence[claim.source_node_id] += 1
                total_influence += 1

        if total_influence == 0:
            return 0.0

        # Calculate HHI
        hhi = 0.0
        for influence in node_influence.values():
            share = influence / total_influence
            hhi += share * share

        return self.validate_range(hhi)


class TopNodeConcentrationCalculator(MetricCalculator):
    """Calculate top node concentration share."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate share of influence from top node."""
        rounds = simulation_data["rounds"]
        node_influence = defaultdict(int)

        # Calculate influence from accepted claims
        for round_data in rounds:
            for claim in round_data.get("accepted_claims", []):
                node_influence[claim.source_node_id] += 1

        if not node_influence:
            return 0.0

        # Find top node's share
        max_influence = max(node_influence.values())
        total_influence = sum(node_influence.values())

        return self.validate_range(max_influence / total_influence if total_influence > 0 else 0.0)


class DomainLeadershipBalanceCalculator(MetricCalculator):
    """Calculate domain leadership balance across nodes."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate balance of domain leadership across nodes."""
        rounds = simulation_data["rounds"]
        domain_leadership = defaultdict(lambda: defaultdict(int))

        # Track claims by domain and node
        for round_data in rounds:
            for claim in round_data.get("accepted_claims", []):
                domain_leadership[claim.domain][claim.source_node_id] += 1

        # Calculate HHI for each domain and average
        hhi_scores = []
        for domain, node_claims in domain_leadership.items():
            total_domain_claims = sum(node_claims.values())
            if total_domain_claims > 0:
                domain_hhi = 0.0
                for claims in node_claims.values():
                    share = claims / total_domain_claims
                    domain_hhi += share * share
                hhi_scores.append(domain_hhi)

        if not hhi_scores:
            return 1.0  # Perfect balance if no data

        # Average HHI across domains (lower = more balanced)
        avg_hhi = sum(hhi_scores) / len(hhi_scores)
        return 1.0 - self.validate_range(avg_hhi)  # Invert so higher = more balanced


class InfluenceBalanceCalculator(MetricCalculator):
    """Calculate overall influence balance index."""

    def __init__(self):
        super().__init__("influence_balance")
        self.sub_calculators = [
            GiniCoefficientCalculator("gini"),
            HerfindahlIndexCalculator("hhi"),
            TopNodeConcentrationCalculator("top_node"),
            DomainLeadershipBalanceCalculator("domain_balance"),
        ]

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate weighted influence balance score."""
        scores = []
        details = {}

        for calculator in self.sub_calculators:
            score = calculator.calculate(simulation_data)
            scores.append(score)
            details[calculator.name] = score

        # Weighted average (inverse for concentration metrics)
        weights = [0.25, 0.25, 0.25, 0.25]  # Equal weights
        balance_score = sum(s * w for s, w in zip(scores, weights))

        # Store details for reporting
        simulation_data["influence_details"] = details

        return self.validate_range(balance_score)


# ============================================================================
# 3. Trust Stability Metrics
# ============================================================================

class TrustDriftCalculator(MetricCalculator):
    """Calculate average trust drift per node."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate average trust drift across all nodes."""
        rounds = simulation_data["rounds"]
        total_drift = 0
        node_drifts = defaultdict(list)

        # Track trust changes over rounds
        for round_data in rounds:
            for node_id, trust_score in round_data.get("node_trust_scores", {}).items():
                node_drifts[node_id].append(trust_score)

        # Calculate drift for each node
        drift_sum = 0
        drift_count = 0

        for node_id, trust_history in node_drifts.items():
            if len(trust_history) > 1:
                first_trust = trust_history[0]
                last_trust = trust_history[-1]
                drift = abs(last_trust - first_trust)
                drift_sum += drift
                drift_count += 1

        if drift_count == 0:
            return 1.0  # No drift = stable

        avg_drift = drift_sum / drift_count
        return 1.0 - self.validate_range(avg_drift)  # Invert so higher = more stable


class TrustVolatilityCalculator(MetricCalculator):
    """Calculate trust volatility index."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate trust volatility across nodes."""
        rounds = simulation_data["rounds"]
        node_volatility = defaultdict(list)

        # Track trust changes over rounds
        for round_data in rounds:
            for node_id, trust_score in round_data.get("node_trust_scores", {}).items():
                node_volatility[node_id].append(trust_score)

        # Calculate volatility (standard deviation) for each node
        volatility_sum = 0
        volatility_count = 0

        for node_id, trust_history in node_volatility.items():
            if len(trust_history) > 1:
                trust_array = np.array(trust_history)
                volatility = np.std(trust_array)
                volatility_sum += volatility
                volatility_count += 1

        if volatility_count == 0:
            return 1.0  # No volatility = stable

        avg_volatility = volatility_sum / volatility_count
        return 1.0 - self.validate_range(avg_volatility)  # Invert so higher = more stable


class AnomalyFrequencyCalculator(MetricCalculator):
    """Calculate anomaly frequency in trust scores."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate rate of trust anomalies detected."""
        rounds = simulation_data["rounds"]
        total_anomalies = 0
        total_checks = 0

        for round_data in rounds:
            anomalies = round_data.get("trust_anomalies", [])
            total_anomalies += len(anomalies)

            # Estimate number of trust checks (nodes in round)
            node_count = len(round_data.get("node_trust_scores", {}))
            total_checks += node_count

        if total_checks == 0:
            return 1.0  # No anomalies = stable

        # Lower anomaly frequency = higher stability
        anomaly_rate = total_anomalies / total_checks
        return 1.0 - self.validate_range(anomaly_rate)


class TrustStabilityCalculator(MetricCalculator):
    """Calculate overall trust stability index."""

    def __init__(self):
        super().__init__("trust_stability")
        self.sub_calculators = [
            TrustDriftCalculator("drift"),
            TrustVolatilityCalculator("volatility"),
            AnomalyFrequencyCalculator("anomaly_rate"),
        ]

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate weighted trust stability score."""
        scores = []
        details = {}

        for calculator in self.sub_calculators:
            score = calculator.calculate(simulation_data)
            scores.append(score)
            details[calculator.name] = score

        # Weighted average
        weights = [0.4, 0.3, 0.3]  # Drift, volatility, anomalies
        stability_score = sum(s * w for s, w in zip(scores, weights))

        # Store details for reporting
        simulation_data["trust_details"] = details

        return self.validate_range(stability_score)


# ============================================================================
# 4. Quality Integrity Metrics
# ============================================================================

class RejectionRateCalculator(MetricCalculator):
    """Calculate claim rejection rate."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate overall rejection rate."""
        rounds = simulation_data["rounds"]
        total_rejected = 0
        total_processed = 0

        for round_data in rounds:
            total_rejected += len(round_data.get("rejected_claims", []))
            total_processed += len(round_data.get("processed_claims", []))

        if total_processed == 0:
            return 1.0  # No rejections = good quality

        return 1.0 - self.validate_range(total_rejected / total_processed)  # Invert


class SpamDetectionRateCalculator(MetricCalculator):
    """Calculate spam detection rate."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate rate of spam claims detected and rejected."""
        rounds = simulation_data["rounds"]
        spam_detected = 0
        total_spam = 0

        for round_data in rounds:
            processed_claims = round_data.get("processed_claims", [])
            for item in processed_claims:
                claim = unwrap_claim(item)
                # Check if rejected (works for both SimulatedClaim and ProcessedSimulationClaimResult)
                is_rejected = not getattr(item, 'accepted', True)

                # Assume claims with very low confidence are potential spam
                if claim.confidence < 0.4:
                    total_spam += 1
                    if is_rejected:
                        spam_detected += 1

        if total_spam == 0:
            return 1.0  # No spam to detect = good

        return self.validate_range(spam_detected / total_spam)


class DuplicateSuppressionRateCalculator(MetricCalculator):
    """Calculate duplicate content suppression rate."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate rate of duplicate claims suppressed."""
        rounds = simulation_data["rounds"]
        duplicates_suppressed = 0
        total_duplicates = 0

        # Track content hashes across rounds
        seen_content = set()

        for round_data in rounds:
            processed_claims = round_data.get("processed_claims", [])
            for item in processed_claims:
                claim = unwrap_claim(item)
                # Check if rejected
                is_rejected = not getattr(item, 'accepted', True)

                # Simple content hash (in production, use proper hash)
                content_hash = hash(claim.content) % 1000000

                if content_hash in seen_content:
                    total_duplicates += 1
                    if is_rejected:
                        duplicates_suppressed += 1
                else:
                    seen_content.add(content_hash)

        if total_duplicates == 0:
            return 1.0  # No duplicates = good

        return self.validate_range(duplicates_suppressed / total_duplicates)


class FalseRejectionRateCalculator(MetricCalculator):
    """Calculate false rejection rate for legitimate content."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate rate of high-quality content incorrectly rejected."""
        rounds = simulation_data["rounds"]
        false_rejections = 0
        total_high_quality = 0

        for round_data in rounds:
            processed_claims = round_data.get("processed_claims", [])
            for item in processed_claims:
                claim = unwrap_claim(item)
                # Check if rejected
                is_rejected = not getattr(item, 'accepted', True)

                quality_score = claim.confidence * claim.provenance_quality

                # Consider high quality if score > 0.7
                if quality_score > 0.7:
                    total_high_quality += 1
                    if is_rejected:
                        false_rejections += 1

        if total_high_quality == 0:
            return 1.0  # No high quality content = no false rejections

        # Lower false rejection rate = better quality integrity
        false_rate = false_rejections / total_high_quality
        return 1.0 - self.validate_range(false_rate)


class QualityIntegrityCalculator(MetricCalculator):
    """Calculate overall quality integrity index."""

    def __init__(self):
        super().__init__("quality_integrity")
        self.sub_calculators = [
            RejectionRateCalculator("rejection_rate"),
            SpamDetectionRateCalculator("spam_detection"),
            DuplicateSuppressionRateCalculator("duplicate_suppression"),
            FalseRejectionRateCalculator("false_rejection"),
        ]

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate weighted quality integrity score."""
        scores = []
        details = {}

        for calculator in self.sub_calculators:
            score = calculator.calculate(simulation_data)
            scores.append(score)
            details[calculator.name] = score

        # Weighted average
        weights = [0.3, 0.3, 0.2, 0.2]  # Rejection, spam, duplicate, false rejection
        integrity_score = sum(s * w for s, w in zip(scores, weights))

        # Store details for reporting
        simulation_data["quality_details"] = details

        return self.validate_range(integrity_score)


# ============================================================================
# 5. Resilience Metrics
# ============================================================================

class ThroughputCalculator(MetricCalculator):
    """Calculate system throughput under load."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate claims processed per round."""
        rounds = simulation_data["rounds"]
        total_processed = 0
        total_rounds = len(rounds)

        if total_rounds == 0:
            return 0.0

        for round_data in rounds:
            total_processed += len(round_data.get("processed_claims", []))

        avg_throughput = total_processed / total_rounds
        return self.validate_range(min(avg_throughput / 10, 1.0))  # Normalize by expected max


class RecoveryTimeCalculator(MetricCalculator):
    """Calculate system recovery time after stress."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate how quickly system recovers from degraded state."""
        rounds = simulation_data["rounds"]

        # Find degradation point (health index drops below 0.7)
        degradation_point = None
        recovery_point = None

        for i, round_data in enumerate(rounds):
            health = round_data.get("federation_health_index", 1.0)
            if health < 0.7 and degradation_point is None:
                degradation_point = i

            if degradation_point is not None and health >= 0.8:
                recovery_point = i
                break

        if degradation_point is None or recovery_point is None:
            return 1.0  # No degradation or recovery needed = resilient

        recovery_time = recovery_point - degradation_point
        # Normalize (longer recovery = less resilient)
        return self.validate_range(1.0 - min(recovery_time / 10, 1.0))


class CascadeFailureCalculator(MetricCalculator):
    """Calculate cascade failure occurrence rate."""

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate rate of cascade failures."""
        rounds = simulation_data["rounds"]
        cascade_failures = 0
        total_rounds = len(rounds)

        # Look for rounds with processing issues
        for round_data in rounds:
            processing_errors = round_data.get("processing_errors", [])
            claim_failures = round_data.get("claim_processing_failures", 0)

            if len(processing_errors) > 2 or claim_failures > 5:
                cascade_failures += 1

        if total_rounds == 0:
            return 1.0  # No failures = resilient

        # Lower cascade failure rate = more resilient
        failure_rate = cascade_failures / total_rounds
        return 1.0 - self.validate_range(failure_rate)


class ResilienceCalculator(MetricCalculator):
    """Calculate overall resilience index."""

    def __init__(self):
        super().__init__("resilience")
        self.sub_calculators = [
            ThroughputCalculator("throughput"),
            RecoveryTimeCalculator("recovery"),
            CascadeFailureCalculator("cascade_failures"),
        ]

    def calculate(self, simulation_data: Dict[str, Any]) -> float:
        """Calculate weighted resilience score."""
        scores = []
        details = {}

        for calculator in self.sub_calculators:
            score = calculator.calculate(simulation_data)
            scores.append(score)
            details[calculator.name] = score

        # Weighted average
        weights = [0.4, 0.4, 0.2]  # Throughput, recovery, cascade failures
        resilience_score = sum(s * w for s, w in zip(scores, weights))

        # Store details for reporting
        simulation_data["resilience_details"] = details

        return self.validate_range(resilience_score)


# ============================================================================
# Main Metrics Aggregator
# ============================================================================

class FederationMetricsAggregator:
    """Aggregates all federation metrics into a comprehensive report."""

    def __init__(self):
        self.category_calculators = {
            "diversity_health": DiversityHealthCalculator(),
            "influence_balance": InfluenceBalanceCalculator(),
            "trust_stability": TrustStabilityCalculator(),
            "quality_integrity": QualityIntegrityCalculator(),
            "resilience": ResilienceCalculator(),
        }

    def calculate_all_metrics(
        self,
        rounds: List[SimulationRound],
        simulation_start: datetime,
        simulation_end: datetime
    ) -> SimulationMetrics:
        """Calculate all metrics and return SimulationMetrics object."""

        # Prepare simulation data
        simulation_data = self._prepare_simulation_data(rounds)

        # Calculate category metrics
        category_scores = {}
        for category, calculator in self.category_calculators.items():
            category_scores[category] = calculator.calculate(simulation_data)

        # Calculate overall health index
        overall_score = sum(
            score * weight
            for category, score in category_scores.items()
            for weight, target_category in [(0.25, "diversity_health"), (0.20, "influence_balance"),
                                           (0.20, "trust_stability"), (0.20, "quality_integrity"),
                                           (0.15, "resilience")]
            if category == target_category
        )

        # Build SimulationMetrics object
        metrics = SimulationMetrics(
            overall_health_index=overall_score,
            diversity_health=category_scores["diversity_health"],
            influence_balance=category_scores["influence_balance"],
            trust_stability=category_scores["trust_stability"],
            quality_integrity=category_scores["quality_integrity"],
            resilience=category_scores["resilience"],
        )

        # Add detailed metrics
        metrics.topic_entropy = simulation_data.get("diversity_details", {}).get("topic_entropy", 0.0)
        metrics.stance_entropy = simulation_data.get("diversity_details", {}).get("stance_entropy", 0.0)
        metrics.gini_coefficient = simulation_data.get("influence_details", {}).get("gini", 0.0)
        metrics.herfindahl_index = simulation_data.get("influence_details", {}).get("hhi", 0.0)
        metrics.average_trust_drift = simulation_data.get("trust_details", {}).get("drift", 0.0)
        metrics.trust_volatility = simulation_data.get("trust_details", {}).get("volatility", 0.0)
        metrics.acceptance_rate = 1.0 - simulation_data.get("quality_details", {}).get("rejection_rate", 0.0)
        metrics.rejection_rate = simulation_data.get("quality_details", {}).get("rejection_rate", 0.0)
        metrics.spam_detected_rate = simulation_data.get("quality_details", {}).get("spam_detection", 0.0)
        metrics.duplicate_suppression_rate = simulation_data.get("quality_details", {}).get("duplicate_suppression", 0.0)

        # Store round history
        metrics.round_history = self._compile_round_history(rounds)

        return metrics

    def _prepare_simulation_data(self, rounds: List[SimulationRound]) -> Dict[str, Any]:
        """Prepare simulation data for metric calculation."""
        simulation_data = {
            "rounds": [],
            "node_claims": defaultdict(int),
        }

        for round_data in rounds:
            round_dict = {
                "number": round_data.round_number,
                "processed_claims": round_data.processed_claims,
                "accepted_claims": round_data.accepted_claims,
                "rejected_claims": round_data.rejected_claims,
                "node_trust_scores": {
                    node.state.node_id: node.state.current_trust
                    for node in round_data.nodes
                },
            }

            # Add metrics if available
            if round_data.diversity_metrics:
                round_dict["diversity_metrics"] = round_data.diversity_metrics
            if round_data.concentration_metrics:
                round_dict["concentration_metrics"] = round_data.concentration_metrics
            if round_data.trust_metrics:
                round_dict["trust_metrics"] = round_data.trust_metrics
            if round_data.quality_metrics:
                round_dict["quality_metrics"] = round_data.quality_metrics

            simulation_data["rounds"].append(round_dict)

        return simulation_data

    def _compile_round_history(self, rounds: List[SimulationRound]) -> List[Dict[str, Any]]:
        """Compile round-by-round history for analysis."""
        history = []

        for round_data in rounds:
            history.append({
                "round": round_data.round_number,
                "total_claims": len(round_data.processed_claims),
                "accepted_claims": len(round_data.accepted_claims),
                "rejected_claims": len(round_data.rejected_claims),
                "acceptance_rate": round_data.get_total_acceptance_rate(),
                "diversity_metrics": round_data.diversity_metrics,
                "concentration_metrics": round_data.concentration_metrics,
                "trust_metrics": round_data.trust_metrics,
                "quality_metrics": round_data.quality_metrics,
            })

        return history


# ============================================================================
# Predictive Metrics Calculators
# ============================================================================

class EpistemicDiversityDecayCalculator:
    """
    Calculates Epistemic Diversity Decay Rate (EDDR).

    EDDR measures how quickly epistemic diversity is shrinking over time.
    This is a leading indicator of network brittleness - collapse often begins
    with quiet diversity erosion before metrics like health index visibly decline.
    """

    def __init__(self, window_size: int = 5):
        """
        Initialize the EDDR calculator.

        Args:
            window_size: Number of rounds to use for decay rate calculation
        """
        self.window_size = window_size

    def calculate(self, round_history: List[Dict[str, Any]]) -> EpistemicDiversityDecayResult:
        """
        Calculate EDDR from round history.

        Args:
            round_history: List of round summary dictionaries

        Returns:
            EpistemicDiversityDecayResult with decay rate and status
        """
        if len(round_history) < 2:
            return self._default_result()

        # Calculate diversity score for each round
        diversity_scores = []
        for round_data in round_history[-self.window_size:]:
            diversity_scores.append(self._calculate_diversity_score(round_data))

        if len(diversity_scores) < 2:
            return self._default_result()

        # Calculate EDDR (slope of diversity over time)
        eddr = (diversity_scores[-1] - diversity_scores[0]) / len(diversity_scores)

        # Determine status
        status = self._determine_status(eddr)

        # Get current values
        latest = round_history[-1]
        topic_entropy = latest.get("diversity_metrics", {}).get("topic_entropy", 0.5)
        stance_entropy = latest.get("diversity_metrics", {}).get("stance_entropy", 0.5)
        minority_ratio = self._calculate_minority_ratio(latest)
        contradiction_retention = self._calculate_contradiction_retention(latest)

        # Generate notes
        notes = []
        if status != PredictiveRiskStatus.HEALTHY:
            notes.append(f"Epistemic diversity declining at {abs(eddr):.3f} per round")
            if eddr < -0.05:
                notes.append("CRITICAL: Diversity collapse risk threshold exceeded")

        # Extract from current round metrics if available
        diversity_details = latest.get("diversity_metrics", {})
        concentration_details = latest.get("concentration_metrics", {})

        return EpistemicDiversityDecayResult(
            current_diversity_score=diversity_scores[-1],
            window_size=min(len(diversity_scores), self.window_size),
            eddr=eddr,
            status=status,
            topic_entropy=topic_entropy,
            stance_entropy=stance_entropy,
            minority_ratio=minority_ratio,
            contradiction_retention=contradiction_retention,
            notes=notes,
        )

    def _calculate_diversity_score(self, round_data: Dict[str, Any]) -> float:
        """Calculate composite diversity score for a round."""
        topic_entropy = round_data.get("diversity_metrics", {}).get("topic_entropy", 0.5)
        stance_entropy = round_data.get("diversity_metrics", {}).get("stance_entropy", 0.5)
        minority_ratio = self._calculate_minority_ratio(round_data)
        contradiction_retention = self._calculate_contradiction_retention(round_data)

        # Weighted composite score
        return (
            0.35 * topic_entropy +
            0.30 * stance_entropy +
            0.20 * minority_ratio +
            0.15 * contradiction_retention
        )

    def _calculate_minority_ratio(self, round_data: Dict[str, Any]) -> float:
        """Calculate the ratio of minority viewpoint contributions."""
        concentration = round_data.get("concentration_metrics", {})
        top_2_share = concentration.get("top_2_share", 0.5)
        return 1.0 - top_2_share  # Minority is what top-2 doesn't control

    def _calculate_contradiction_retention(self, round_data: Dict[str, Any]) -> float:
        """Calculate how well contradiction is being preserved."""
        # Estimate from stance entropy - high stance entropy with multiple stances
        # suggests healthy contradiction is present
        stance_entropy = round_data.get("diversity_metrics", {}).get("stance_entropy", 0.5)
        return min(1.0, stance_entropy * 1.5)  # Scale up slightly

    def _determine_status(self, eddr: float) -> PredictiveRiskStatus:
        """Determine risk status from EDDR value."""
        if eddr > -0.01:
            return PredictiveRiskStatus.HEALTHY
        elif eddr > -0.03:
            return PredictiveRiskStatus.WATCH
        elif eddr > -0.05:
            return PredictiveRiskStatus.DEGRADING
        else:
            return PredictiveRiskStatus.COLLAPSE_RISK

    def _default_result(self) -> EpistemicDiversityDecayResult:
        """Return default result when insufficient data."""
        return EpistemicDiversityDecayResult(
            current_diversity_score=0.8,
            window_size=0,
            eddr=0.0,
            status=PredictiveRiskStatus.HEALTHY,
            topic_entropy=0.5,
            stance_entropy=0.5,
            minority_ratio=0.5,
            contradiction_retention=0.5,
            notes=["Insufficient data for EDDR calculation"],
        )


class AuthorityCaptureAccelerationCalculator:
    """
    Calculates Authority Capture Acceleration (ACA).

    ACA measures how quickly influence is concentrating into a small number of nodes.
    This is an early warning signal - authority capture almost always precedes
    diversity collapse, so ACA provides earlier warning than EDDR alone.
    """

    def __init__(self, window_size: int = 5):
        """
        Initialize the ACA calculator.

        Args:
            window_size: Number of rounds to use for acceleration calculation
        """
        self.window_size = window_size

    def calculate(self, round_history: List[Dict[str, Any]]) -> AuthorityCaptureAccelerationResult:
        """
        Calculate ACA from round history.

        Args:
            round_history: List of round summary dictionaries

        Returns:
            AuthorityCaptureAccelerationResult with acceleration and status
        """
        if len(round_history) < 2:
            return self._default_result()

        # Calculate concentration score for each round
        concentration_scores = []
        for round_data in round_history[-self.window_size:]:
            concentration_scores.append(self._calculate_concentration_score(round_data))

        if len(concentration_scores) < 2:
            return self._default_result()

        # Calculate ACA (slope of concentration over time)
        aca = (concentration_scores[-1] - concentration_scores[0]) / len(concentration_scores)

        # Determine status
        status = self._determine_status(aca)

        # Get current values
        latest = round_history[-1]
        gini = latest.get("concentration_metrics", {}).get("gini", 0.3)
        hhi = latest.get("concentration_metrics", {}).get("hhi", 0.15)
        top_1_share = latest.get("concentration_metrics", {}).get("top_1_share", 0.2)
        top_2_share = latest.get("concentration_metrics", {}).get("top_2_share", 0.35)

        # Identify dominant nodes
        dominant_nodes = self._identify_dominant_nodes(latest)
        dominant_domains = self._identify_dominant_domains(latest)

        # Generate notes
        notes = []
        if status != PredictiveRiskStatus.HEALTHY:
            notes.append(f"Authority influence concentrating at {aca:.3f} per round")
            if aca > 0.05:
                notes.append("CRITICAL: Authority capture threshold exceeded")

        return AuthorityCaptureAccelerationResult(
            current_concentration_score=concentration_scores[-1],
            window_size=min(len(concentration_scores), self.window_size),
            aca=aca,
            status=status,
            gini=gini,
            hhi=hhi,
            top_1_share=top_1_share,
            top_2_share=top_2_share,
            dominant_nodes=dominant_nodes,
            dominant_domains=dominant_domains,
            notes=notes,
        )

    def _calculate_concentration_score(self, round_data: Dict[str, Any]) -> float:
        """Calculate composite concentration score."""
        gini = round_data.get("concentration_metrics", {}).get("gini", 0.3)
        hhi = round_data.get("concentration_metrics", {}).get("hhi", 0.15)
        top_1_share = round_data.get("concentration_metrics", {}).get("top_1_share", 0.2)
        top_2_share = round_data.get("concentration_metrics", {}).get("top_2_share", 0.35)

        # Normalize HHI to 0-1 scale (HHI max is 1.0)
        normalized_hhi = min(1.0, hhi * 4)  # HHI 0.25 -> 1.0

        # Weighted composite score
        return (
            0.35 * gini +
            0.35 * normalized_hhi +
            0.20 * top_1_share +
            0.10 * top_2_share
        )

    def _identify_dominant_nodes(self, round_data: Dict[str, Any]) -> List[str]:
        """Identify dominant nodes from acceptance data."""
        # This would need detailed claim-by-node tracking
        # For now, infer from concentration metrics
        top_nodes = []
        if round_data.get("concentration_metrics", {}).get("top_1_share", 0.0) > 0.30:
            top_nodes.append("dominant_node_1")
        return top_nodes

    def _identify_dominant_domains(self, round_data: Dict[str, Any]) -> List[str]:
        """Identify domains with high concentration."""
        # Would need domain-specific tracking
        return []

    def _determine_status(self, aca: float) -> PredictiveRiskStatus:
        """Determine risk status from ACA value."""
        if aca < 0.01:
            return PredictiveRiskStatus.HEALTHY
        elif aca < 0.03:
            return PredictiveRiskStatus.WATCH
        elif aca < 0.05:
            return PredictiveRiskStatus.DEGRADING
        else:
            return PredictiveRiskStatus.COLLAPSE_RISK

    def _default_result(self) -> AuthorityCaptureAccelerationResult:
        """Return default result when insufficient data."""
        return AuthorityCaptureAccelerationResult(
            current_concentration_score=0.3,
            window_size=0,
            aca=0.0,
            status=PredictiveRiskStatus.HEALTHY,
            gini=0.3,
            hhi=0.15,
            top_1_share=0.2,
            top_2_share=0.35,
            dominant_nodes=[],
            dominant_domains=[],
            notes=["Insufficient data for ACA calculation"],
        )


class FederationCollapseRiskCalculator:
    """
    Calculates Federation Collapse Risk Index (FCRI).

    FCRI combines EDDR and ACA into a single predictive governance signal.
    This is the primary early warning metric for distributed epistemic collapse.
    """

    def __init__(self):
        """Initialize the FCRI calculator."""
        self.eddr_calculator = EpistemicDiversityDecayCalculator()
        self.aca_calculator = AuthorityCaptureAccelerationCalculator()

    def calculate(
        self,
        eddr_result: EpistemicDiversityDecayResult,
        aca_result: AuthorityCaptureAccelerationResult,
    ) -> FederationCollapseRiskResult:
        """
        Calculate FCRI from EDDR and ACA results.

        Args:
            eddr_result: EDDR calculation result
            aca_result: ACA calculation result

        Returns:
            FederationCollapseRiskResult with composite risk index
        """
        # Calculate FCRI: only positive ACA and negative EDDR contribute to risk
        fcri = 0.6 * max(aca_result.aca, 0) + 0.4 * abs(min(eddr_result.eddr, 0))

        # Determine status
        status = self._determine_status(fcri, eddr_result, aca_result)

        # Determine primary driver
        primary_driver = self._determine_primary_driver(eddr_result, aca_result, fcri)

        # Generate recommended actions
        recommended_actions = self._generate_recommendations(
            fcri, eddr_result, aca_result, primary_driver
        )

        # Combine dominant nodes and domains
        dominant_nodes = list(set(eddr_result.dominant_nodes + aca_result.dominant_nodes))
        dominant_domains = list(set(eddr_result.dominant_domains + aca_result.dominant_domains))

        return FederationCollapseRiskResult(
            fcri=fcri,
            status=status,
            primary_driver=primary_driver,
            eddr=eddr_result.eddr,
            aca=aca_result.aca,
            dominant_nodes=dominant_nodes,
            dominant_domains=dominant_domains,
            recommended_actions=recommended_actions,
        )

    def _determine_status(
        self,
        fcri: float,
        eddr_result: EpistemicDiversityDecayResult,
        aca_result: AuthorityCaptureAccelerationResult,
    ) -> PredictiveRiskStatus:
        """Determine overall risk status."""
        if fcri < 0.02:
            return PredictiveRiskStatus.HEALTHY
        elif fcri < 0.05:
            return PredictiveRiskStatus.WATCH
        elif fcri < 0.08:
            return PredictiveRiskStatus.DEGRADING
        else:
            return PredictiveRiskStatus.COLLAPSE_RISK

    def _determine_primary_driver(
        self,
        eddr_result: EpistemicDiversityDecayResult,
        aca_result: AuthorityCaptureAccelerationResult,
        fcri: float,
    ) -> str:
        """Determine what's driving the risk."""
        if aca_result.aca > 0.05 and eddr_result.eddr < -0.03:
            return "authority_capture"
        elif eddr_result.eddr < -0.05 and aca_result.aca < 0.03:
            return "diversity_decay"
        elif aca_result.aca > 0.03 and eddr_result.eddr < -0.03:
            return "combined"
        else:
            return "none"

    def _generate_recommendations(
        self,
        fcri: float,
        eddr_result: EpistemicDiversityDecayResult,
        aca_result: AuthorityCaptureAccelerationResult,
        primary_driver: str,
    ) -> List[str]:
        """Generate actionable recommendations based on risk assessment."""
        recommendations = []

        if fcri > 0.05:
            recommendations.append("CRITICAL: Federation collapse risk detected - immediate intervention required")

        if primary_driver == "authority_capture":
            recommendations.append("Strengthen allocative throttling on dominant nodes")
            recommendations.append("Consider reducing trust weight of concentrated nodes")
            recommendations.append("Amplify minority perspectives in affected domains")
        elif primary_driver == "diversity_decay":
            recommendations.append("Increase context similarity sensitivity for emerging clusters")
            recommendations.append("Force diversity preservation in qualification engine")
            recommendations.append("Amplify contradictory but high-quality minority claims")
        elif primary_driver == "combined":
            recommendations.append("Multi-faceted intervention required - both authority and diversity safeguards")
            recommendations.append("Consider emergency throttling of top nodes")
            recommendations.append("Review and widen plurality preservation thresholds")

        # Add scenario-specific recommendations based on status
        if eddr_result.status == PredictiveRiskStatus.COLLAPSE_RISK:
            recommendations.append("Diversity at collapse threshold - emergency intervention needed")
        if aca_result.status == PredictiveRiskStatus.COLLAPSE_RISK:
            recommendations.append("Authority capture critical - redistribute domain leadership")

        return recommendations