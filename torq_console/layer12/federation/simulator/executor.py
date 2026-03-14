"""
Federation Simulation Executor

Layer 12 Phase 2A — Federation Stability Validation Harness

Round executor that routes claims through InboundFederatedClaimProcessor
and manages the complete simulation lifecycle.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    Domain,
    NodeBehaviorProfile,
    NodeState,
    SimulatedClaim,
    SimulatedNode,
    SimulationRound,
    SimulationScenario,
    SimulationReport,
    SimulationMetrics,
)
from ..inbound_claim_processor import InboundFederatedClaimProcessor, ProcessorConfig
from ..safeguards import (
    create_eligibility_filter,
    create_context_similarity_engine,
    create_plurality_preservation_rules,
    create_allocative_boundary_guard,
    create_trust_decay_model,
)
from .metrics import FederationMetricsAggregator
from .health_index import FederationHealthIndexCalculator

logger = logging.getLogger(__name__)


# ============================================================================
# Simulation Executor
# ============================================================================

class FederationSimulationExecutor:
    """Main simulation executor that runs federation scenarios."""

    def __init__(
        self,
        processor_config: Optional[ProcessorConfig] = None,
        enable_all_safeguards: bool = True,
        enable_metrics: bool = True,
        enable_health_index: bool = True,
    ):
        self.processor_config = processor_config or ProcessorConfig()
        self.enable_all_safeguards = enable_all_safeguards
        self.enable_metrics = enable_metrics
        self.enable_health_index = enable_health_index

        # Initialize processor with safeguards
        self.processor = self._initialize_processor()

        # Initialize metrics
        self.metrics_aggregator = FederationMetricsAggregator() if enable_metrics else None
        self.health_calculator = FederationHealthIndexCalculator() if enable_health_index else None

        # Simulation state
        self.current_round = 0
        self.simulation_start_time: Optional[datetime] = None
        self.simulation_end_time: Optional[datetime] = None
        self.round_results: List[SimulationRound] = []

        # Statistics
        self.total_claims_generated = 0
        self.total_claims_processed = 0
        self.total_claims_accepted = 0
        self.total_claims_rejected = 0
        self.safeguard_triggers = {}

        logger.info("FederationSimulationExecutor initialized")

    def _initialize_processor(self) -> InboundFederatedClaimProcessor:
        """Initialize the claim processor with safeguards."""
        # Import FederationIdentityGuard for required parameter
        from ..federation_identity_guard import FederationIdentityGuard
        from ..config import FederationConfig

        # Create identity guard (required for processor)
        identity_guard = FederationIdentityGuard()

        # Create safeguards if enabled
        eligibility_filter = None
        similarity_engine = None
        plurality_rules = None
        allocative_guard = None
        trust_decay = None

        if self.enable_all_safeguards:
            eligibility_filter = create_eligibility_filter()
            similarity_engine = create_context_similarity_engine()
            plurality_rules = create_plurality_preservation_rules()
            allocative_guard = create_allocative_boundary_guard()
            trust_decay = create_trust_decay_model()

        # Initialize processor
        processor = InboundFederatedClaimProcessor(
            identity_guard=identity_guard,
            config=self.processor_config,
            federation_config=FederationConfig(),
            eligibility_filter=eligibility_filter,
            similarity_engine=similarity_engine,
            plurality_rules=plurality_rules,
            allocative_guard=allocative_guard,
            trust_decay=trust_decay,
        )

        return processor

    def run_simulation(
        self,
        scenario: SimulationScenario,
        dry_run: bool = False,
        verbose: bool = False
    ) -> SimulationReport:
        """Run a complete simulation for the given scenario."""

        if dry_run:
            logger.info(f"Dry run: {scenario.name}")
            return self._dry_run_scenario(scenario)

        logger.info(f"Starting simulation: {scenario.name}")
        logger.info(f"Nodes: {scenario.num_nodes}, Rounds: {scenario.rounds}")

        # Initialize simulation
        self.simulation_start_time = datetime.utcnow()
        self.round_results = []
        self.current_round = 0

        # Create nodes
        nodes = self._create_nodes(scenario)

        # Run simulation rounds
        for round_num in range(scenario.rounds):
            self.current_round = round_num + 1
            round_start = time.time()

            if verbose:
                logger.info(f"Round {round_num + 1}/{scenario.rounds}")

            # Run round
            round_result = self._run_round(
                round_num=round_num,
                nodes=nodes,
                scenario=scenario,
                verbose=verbose
            )

            self.round_results.append(round_result)

            # Update node trust based on processing results
            self._update_node_trust(round_result)

            # Log round summary
            round_time = time.time() - round_start
            if verbose:
                logger.info(
                    f"Round {round_num + 1} completed in {round_time:.2f}s: "
                    f"Generated={len(round_result.claims)}, "
                    f"Accepted={len(round_result.accepted_claims)}, "
                    f"Rejected={len(round_result.rejected_claims)}, "
                    f"Acceptance Rate={round_result.get_total_acceptance_rate():.2%}"
                )

        # Finalize simulation
        self.simulation_end_time = datetime.utcnow()

        # Calculate metrics
        metrics = self._calculate_final_metrics()

        # Generate report
        report = self._generate_report(scenario, metrics)

        # Log summary
        logger.info(f"Simulation completed: {scenario.name}")
        logger.info(f"Overall Health Index: {metrics.overall_health_index:.3f}")
        logger.info(f"Status: {report.scenario.name} - {report.failure_points or 'Success'}")

        return report

    def _create_nodes(self, scenario: SimulationScenario) -> List[SimulatedNode]:
        """Create simulated nodes based on scenario configuration."""
        nodes = []
        available_domains = list(scenario.domain_distribution.keys())

        for i in range(scenario.num_nodes):
            node_id = f"node_{i}"

            # Get node type
            node_type = scenario.node_types[i] if i < len(scenario.node_types) else NodeType.NORMAL

            # Check if node is adversarial
            is_adversarial = node_id in scenario.adversarial_nodes
            adversarial_mode = scenario.adversarial_modes.get(node_id) if is_adversarial else None

            # Create behavior profile
            profile = NodeBehaviorProfile(
                node_type=node_type,
                is_adversarial=is_adversarial,
                adversarial_mode=adversarial_mode,
                # Set different baseline trusts for variety
                baseline_trust=0.5 + (i * 0.1),  # Spread from 0.5 to 0.9
            )

            # Create node
            node = SimulatedNode(node_id, profile)
            nodes.append(node)

            logger.debug(f"Created node {node_id}: type={node_type}, adversarial={is_adversarial}")

        return nodes

    def _run_round(
        self,
        round_num: int,
        nodes: List[SimulatedNode],
        scenario: SimulationScenario,
        verbose: bool = False
    ) -> SimulationRound:
        """Run a single simulation round."""

        # Create round
        round_data = SimulationRound(
            round_number=round_num + 1,
            nodes=nodes,
            claims=[],
            round_start_time=datetime.utcnow(),
        )

        # Generate claims for each node
        for node in nodes:
            # Generate claims based on node profile
            num_claims = self._generate_claim_count(node, scenario)

            for _ in range(num_claims):
                claim = node.generate_claim(round_num + 1, list(scenario.domain_distribution.keys()))
                round_data.claims.append(claim)
                self.total_claims_generated += 1

                # Add adversarial claim modifications if needed
                claim = self._modify_adversarial_claim(claim, scenario)

        # Process claims through federation pipeline
        processed_claims = self._process_claims(round_data.claims)

        # Update round results
        for claim, result in processed_claims:
            round_data.add_processed_claim(claim, result.decision)

            # Track safeguard triggers
            for safeguard_name, trigger_info in result.safeguard_results.items():
                if trigger_info.triggered:
                    self.safeguard_triggers[safeguard_name] = self.safeguard_triggers.get(safeguard_name, 0) + 1

        # Calculate round metrics
        if self.enable_metrics and self.metrics_aggregator:
            round_metrics = self._calculate_round_metrics(round_data)
            round_data.diversity_metrics = round_metrics.get("diversity", {})
            round_data.concentration_metrics = round_metrics.get("concentration", {})
            round_data.trust_metrics = round_metrics.get("trust", {})
            round_data.quality_metrics = round_metrics.get("quality", {})

        # Update statistics
        self.total_claims_processed += len(round_data.processed_claims)
        self.total_claims_accepted += len(round_data.accepted_claims)
        self.total_claims_rejected += len(round_data.rejected_claims)

        return round_data

    def _generate_claim_count(self, node: SimulatedNode, scenario: SimulationScenario) -> int:
        """Generate number of claims for a node in a round."""
        base_rate = node.profile.base_claim_rate

        # Adversarial adjustments
        if node.profile.is_adversarial:
            if node.profile.adversarial_mode == "flood":
                return int(base_rate * 5)  # Flood node produces 5x more claims
            elif node.profile.adversarial_mode == "monoculture":
                return int(base_rate * 2)  # Monoculture node produces 2x more claims

        return int(base_rate)

    def _modify_adversarial_claim(self, claim: SimulatedClaim, scenario: SimulationScenario) -> SimulatedClaim:
        """Modify claims for adversarial nodes."""
        if claim.source_node_id not in scenario.adversarial_nodes:
            return claim

        adversarial_mode = scenario.adversarial_modes.get(claim.source_node_id)

        if adversarial_mode == "flood":
            # Lower quality for flood attack
            claim.confidence *= 0.7
            claim.provenance_quality *= 0.7
        elif adversarial_mode == "monoculture":
            # Force specific domain
            claim.domain = Domain.SECURITY  # Force security domain for monoculture
        elif adversarial_mode == "replay":
            # Mark as potential replay
            claim.is_replay = True
        elif adversarial_mode == "trust_gaming":
            # High confidence but low quality
            claim.confidence = 0.9
            claim.provenance_quality = 0.4

        return claim

    def _process_claims(self, claims: List[SimulatedClaim]) -> List[Tuple[SimulatedClaim, Any]]:
        """Process claims through the federation pipeline."""
        results = []

        for claim in claims:
            try:
                # Convert to federated payload
                payload = claim.to_federated_payload()

                # Process through federation pipeline
                result = self.processor.process_federated_claim(payload)

                # Store result
                claim.processing_result = result
                claim.final_decision = result.decision
                claim.trusted_after_processing = result.trusted_after_processing

                results.append((claim, result))

            except Exception as e:
                logger.error(f"Error processing claim {claim.claim_id}: {e}")
                # Mark as rejected on error
                claim.final_decision = "reject"
                results.append((claim, None))

        return results

    def _update_node_trust(self, round_data: SimulationRound):
        """Update node trust scores based on processing results."""
        for claim in round_data.processed_claims:
            if claim.source_node_id in self.processor.node_trust:
                # Update trust in processor
                self.processor.node_trust[claim.source_node_id] = claim.trusted_after_processing

    def _calculate_round_metrics(self, round_data: SimulationRound) -> Dict[str, Dict[str, float]]:
        """Calculate metrics for a single round."""
        if not self.metrics_aggregator:
            return {}

        # Create temporary simulation data for this round
        simulation_data = {
            "rounds": [{
                "number": round_data.round_number,
                "processed_claims": round_data.processed_claims,
                "accepted_claims": round_data.accepted_claims,
                "rejected_claims": round_data.rejected_claims,
                "node_trust_scores": {
                    node.state.node_id: node.state.current_trust
                    for node in round_data.nodes
                },
            }]
        }

        # Calculate category metrics
        metrics = {}

        # Diversity metrics
        topic_entropy = self._calculate_topic_entropy(round_data.accepted_claims)
        stance_entropy = self._calculate_stance_entropy(round_data.accepted_claims)
        metrics["diversity"] = {
            "topic_entropy": topic_entropy,
            "stance_entropy": stance_entropy,
        }

        # Concentration metrics
        gini = self._calculate_gini_coefficient(round_data.accepted_claims)
        hhi = self._calculate_hhi(round_data.accepted_claims)
        metrics["concentration"] = {
            "gini_coefficient": gini,
            "herfindahl_index": hhi,
        }

        # Trust metrics
        trust_drift = self._calculate_trust_drift(round_data.nodes)
        trust_volatility = self._calculate_trust_volatility(round_data.nodes)
        metrics["trust"] = {
            "trust_drift": trust_drift,
            "trust_volatility": trust_volatility,
        }

        # Quality metrics
        rejection_rate = len(round_data.rejected_claims) / max(len(round_data.processed_claims), 1)
        metrics["quality"] = {
            "rejection_rate": rejection_rate,
        }

        return metrics

    def _calculate_topic_entropy(self, claims: List[SimulatedClaim]) -> float:
        """Calculate topic entropy for accepted claims."""
        if not claims:
            return 0.0

        domain_counts = defaultdict(int)
        for claim in claims:
            domain_counts[claim.domain] += 1

        # Calculate Shannon entropy
        entropy = 0.0
        total = len(claims)
        for count in domain_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        # Normalize
        max_entropy = math.log2(len(domain_counts))
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _calculate_stance_entropy(self, claims: List[SimulatedClaim]) -> float:
        """Calculate stance entropy for accepted claims."""
        if not claims:
            return 0.0

        stance_counts = defaultdict(int)
        for claim in claims:
            stance_counts[claim.stance] += 1

        # Calculate Shannon entropy
        entropy = 0.0
        total = len(claims)
        for count in stance_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        # Normalize
        max_entropy = math.log2(len(stance_counts))
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _calculate_gini_coefficient(self, claims: List[SimulatedClaim]) -> float:
        """Calculate Gini coefficient for node influence."""
        if not claims:
            return 0.0

        node_influence = defaultdict(int)
        for claim in claims:
            node_influence[claim.source_node_id] += 1

        if len(node_influence) == 1:
            return 0.0

        # Calculate Gini coefficient
        sorted_influences = sorted(node_influence.values())
        n = len(sorted_influences)
        total_influence = sum(sorted_influences)

        cum_sum = 0
        for i, influence in enumerate(sorted_influences):
            cum_sum += influence
            gini = (2 * (i + 1) - n - 1) * influence
            gini /= n * total_influence

        return abs(gini) * n / (n - 1)

    def _calculate_hhi(self, claims: List[SimulatedClaim]) -> float:
        """Calculate Herfindahl-Hirschman Index."""
        if not claims:
            return 0.0

        node_influence = defaultdict(int)
        for claim in claims:
            node_influence[claim.source_node_id] += 1

        total_influence = sum(node_influence.values())
        hhi = 0.0

        for influence in node_influence.values():
            share = influence / total_influence
            hhi += share * share

        return hhi

    def _calculate_trust_drift(self, nodes: List[SimulatedNode]) -> float:
        """Calculate average trust drift across nodes."""
        if not nodes:
            return 0.0

        # This would normally track trust over time, for now return baseline
        return 0.0

    def _calculate_trust_volatility(self, nodes: List[SimulatedNode]) -> float:
        """Calculate trust volatility across nodes."""
        if not nodes:
            return 0.0

        # Calculate standard deviation of trust scores
        trust_scores = [node.state.current_trust for node in nodes]
        mean = sum(trust_scores) / len(trust_scores)
        variance = sum((t - mean) ** 2 for t in trust_scores) / len(trust_scores)
        return variance ** 0.5

    def _calculate_final_metrics(self) -> SimulationMetrics:
        """Calculate final simulation metrics."""
        if not self.metrics_aggregator:
            return SimulationMetrics()

        return self.metrics_aggregator.calculate_all_metrics(
            rounds=self.round_results,
            simulation_start=self.simulation_start_time,
            simulation_end=self.simulation_end_time,
        )

    def _generate_report(
        self,
        scenario: SimulationScenario,
        metrics: SimulationMetrics
    ) -> SimulationReport:
        """Generate simulation report."""
        # Calculate execution time
        if self.simulation_start_time and self.simulation_end_time:
            execution_time = self.simulation_end_time - self.simulation_start_time
        else:
            execution_time = timedelta(0)

        # Calculate success rate
        success_rate = self._calculate_success_rate(scenario, metrics)

        # Create report
        report = SimulationReport(
            scenario=scenario,
            metrics=metrics,
            execution_time=execution_time,
            success_rate=success_rate,
        )

        # Add safeguard triggers
        for guardian_name, count in self.safeguard_triggers.items():
            report.add_guardian_trigger(guardian_name, count)

        # Calculate effectiveness
        report.calculate_safeguard_effectiveness()

        # Identify failure points
        report.failure_points = self._identify_failure_points(metrics, scenario)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(metrics)

        return report

    def _calculate_success_rate(
        self,
        scenario: SimulationScenario,
        metrics: SimulationMetrics
    ) -> float:
        """Calculate simulation success rate."""
        # Check against expected outcomes
        success_criteria_met = 0
        total_criteria = 0

        for expected_key, expected_value in scenario.expected_outcomes.items():
            if expected_key == "health_status":
                # Compare overall health status
                if metrics.overall_health_index >= 0.85:
                    actual_status = "healthy"
                elif metrics.overall_health_index >= 0.70:
                    actual_status = "stable"
                elif metrics.overall_health_index >= 0.50:
                    actual_status = "degraded"
                else:
                    actual_status = "failing"

                if actual_status == expected_value:
                    success_criteria_met += 1
            else:
                # Compare metric values
                actual_value = getattr(metrics, expected_key, None)
                if actual_value is not None:
                    if expected_value.startswith(">"):
                        threshold = float(expected_value[1:])
                        if actual_value >= threshold:
                            success_criteria_met += 1
                    elif expected_value.startswith("<"):
                        threshold = float(expected_value[1:])
                        if actual_value <= threshold:
                            success_criteria_met += 1
                    else:
                        # Direct comparison
                        if str(actual_value) == expected_value:
                            success_criteria_met += 1

            total_criteria += 1

        return success_criteria_met / max(total_criteria, 1)

    def _identify_failure_points(
        self,
        metrics: SimulationMetrics,
        scenario: SimulationScenario
    ) -> List[str]:
        """Identify failure points in the simulation."""
        failure_points = []

        # Check overall health
        if metrics.overall_health_index < 0.50:
            failure_points.append("Federation health index critical")

        # Check category failures
        if metrics.diversity_health < 0.50:
            failure_points.append("Diversity health severely degraded")
        if metrics.influence_balance < 0.50:
            failure_points.append("Influence balance severely compromised")
        if metrics.trust_stability < 0.50:
            failure_points.append("Trust stability severely compromised")
        if metrics.quality_integrity < 0.50:
            failure_points.append("Quality integrity severely compromised")
        if metrics.resilience < 0.50:
            failure_points.append("Resilience severely compromised")

        # Check specific metrics
        if metrics.gini_coefficient > 0.7:
            failure_points.append("Extreme authority concentration detected")
        if metrics.topic_entropy < 0.5:
            failure_points.append("Severe topic monoculture detected")
        if metrics.trust_volatility > 0.4:
            failure_points.append("Extreme trust volatility detected")

        return failure_points

    def _generate_recommendations(self, metrics: SimulationMetrics) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        # Overall recommendations
        if metrics.overall_health_index < 0.70:
            recommendations.append("Consider federation throttling to prevent overload")

        # Category-specific recommendations
        if metrics.diversity_health < 0.70:
            recommendations.append("Review diversity safeguards - consider adjusting PluralityPreservationRules")
        if metrics.influence_balance < 0.70:
            recommendations.append("Tighten AllocativeBoundaryGuard thresholds to reduce concentration")
        if metrics.trust_stability < 0.70:
            recommendations.append("Increase TrustDecayModel sensitivity for better anomaly detection")
        if metrics.quality_integrity < 0.70:
            recommendations.append("Calibrate FederationEligibilityFilter parameters")
        if metrics.resilience < 0.70:
            recommendations.append("Implement circuit breakers for high-volume scenarios")

        return recommendations

    def _dry_run_scenario(self, scenario: SimulationScenario) -> SimulationReport:
        """Perform a dry run of the scenario to validate configuration."""
        logger.info(f"Dry run for {scenario.name}")

        # Create report with placeholder data
        metrics = SimulationMetrics(
            overall_health_index=0.0,
            diversity_health=0.0,
            influence_balance=0.0,
            trust_stability=0.0,
            quality_integrity=0.0,
            resilience=0.0,
        )

        execution_time = timedelta(0)
        success_rate = 0.0

        report = SimulationReport(
            scenario=scenario,
            metrics=metrics,
            execution_time=execution_time,
            success_rate=success_rate,
        )

        # Add validation notes
        validation_notes = []
        validation_notes.append(f"Scenario: {scenario.name}")
        validation_notes.append(f"Nodes: {scenario.num_nodes}")
        validation_notes.append(f"Rounds: {scenario.rounds}")
        validation_notes.append(f"Adversarial nodes: {len(scenario.adversarial_nodes)}")

        if scenario.expected_guardian_triggers:
            validation_notes.append(f"Expected guardians: {', '.join(scenario.expected_guardian_triggers)}")

        report.recommendations = validation_notes

        return report

    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation execution statistics."""
        return {
            "total_rounds": len(self.round_results),
            "total_claims_generated": self.total_claims_generated,
            "total_claims_processed": self.total_claims_processed,
            "total_claims_accepted": self.total_claims_accepted,
            "total_claims_rejected": self.total_claims_rejected,
            "acceptance_rate": self.total_claims_accepted / max(self.total_claims_processed, 1),
            "safeguard_triggers": self.safeguard_triggers,
            "simulation_duration": (
                self.simulation_end_time - self.simulation_start_time
                if self.simulation_start_time and self.simulation_end_time
                else None
            ),
        }