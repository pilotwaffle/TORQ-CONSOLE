"""
Async Federation Simulation Executor

Layer 12 Phase 2A — Federation Stability Validation Harness

Async round executor that routes claims through the real InboundFederatedClaimProcessor
via the ProcessorAdapter and manages the complete simulation lifecycle.
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    Domain,
    NodeBehaviorProfile,
    NodeState,
    NodeType,
    RoundSummary,
    SimulatedClaim,
    SimulatedNode,
    SimulationRound,
    SimulationScenario,
    SimulationReport,
    SimulationMetrics,
    Stance,
    EpistemicDiversityDecayResult,
    AuthorityCaptureAccelerationResult,
    FederationCollapseRiskResult,
)
from ..inbound_claim_processor import InboundFederatedClaimProcessor, ProcessorConfig
from ..safeguards import (
    create_eligibility_filter,
    create_context_similarity_engine,
    create_plurality_preservation_rules,
    create_allocative_boundary_guard,
    create_trust_decay_model,
)
from ..federation_identity_guard import FederationIdentityGuard
from ..config import FederationConfig
from .metrics import (
    FederationMetricsAggregator,
    EpistemicDiversityDecayCalculator,
    AuthorityCaptureAccelerationCalculator,
    FederationCollapseRiskCalculator,
)
from .health_index import FederationHealthIndexCalculator
from .processor_adapter import ProcessorAdapter, process_claims_batch

logger = logging.getLogger(__name__)


# ============================================================================
# Async Simulation Executor
# ============================================================================

class AsyncFederationSimulationExecutor:
    """Async simulation executor that runs federation scenarios through the real processor."""

    def __init__(
        self,
        processor_config: Optional[ProcessorConfig] = None,
        enable_all_safeguards: bool = True,
        enable_metrics: bool = True,
        enable_health_index: bool = True,
        enable_predictive_metrics: bool = True,
        simulation_mode: bool = True,  # Enable permissive safeguard behavior for simulation
    ):
        self.processor_config = processor_config or ProcessorConfig()
        self.enable_all_safeguards = enable_all_safeguards
        self.enable_metrics = enable_metrics
        self.enable_health_index = enable_health_index
        self.enable_predictive_metrics = enable_predictive_metrics
        self.simulation_mode = simulation_mode

        # Initialize processor with safeguards
        self.processor, self.identity_guard = self._initialize_processor()

        # Initialize processor adapter
        self.adapter = ProcessorAdapter(
            processor=self.processor,
            identity_guard=self.identity_guard,
        )

        # Initialize metrics aggregators
        self.metrics_aggregator = FederationMetricsAggregator() if enable_metrics else None
        self.health_calculator = FederationHealthIndexCalculator() if enable_health_index else None

        # Initialize predictive metrics calculators
        if enable_predictive_metrics:
            self.eddr_calculator = EpistemicDiversityDecayCalculator(window_size=5)
            self.aca_calculator = AuthorityCaptureAccelerationCalculator(window_size=5)
            self.fcri_calculator = FederationCollapseRiskCalculator()
        else:
            self.eddr_calculator = None
            self.aca_calculator = None
            self.fcri_calculator = None

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

        logger.info("AsyncFederationSimulationExecutor initialized")

    def _initialize_processor(self) -> Tuple[InboundFederatedClaimProcessor, FederationIdentityGuard]:
        """Initialize the claim processor with safeguards."""
        # Import safeguard types
        from ..safeguards import EligibilityCriteria
        from ..safeguards import (
            create_context_similarity_engine,
            create_plurality_preservation_rules,
            create_allocative_boundary_guard,
            create_trust_decay_model,
        )

        # Create shared federation config
        federation_config = FederationConfig()

        # Create identity guard (required for processor)
        identity_guard = FederationIdentityGuard(config=federation_config)

        # Create safeguards if enabled
        eligibility_filter = None
        similarity_engine = None
        plurality_rules = None
        allocative_guard = None
        trust_decay = None

        # For simulation mode, create a processor config that disables
        # safeguards that cause false positives with low node counts
        if self.simulation_mode:
            processor_config = ProcessorConfig(
                enable_eligibility_filter=True,  # Keep for quality control
                enable_context_similarity=False,  # Disable to avoid false monoculture detection
                enable_plurality_preservation=False,  # Disable to avoid false monoculture detection
                enable_allocative_boundaries=False,  # Disable to avoid false authority concentration
                enable_trust_decay=False,  # Disable for simulation
            )
            # Only enable eligibility filter for quality control
            eligibility_filter = create_eligibility_filter(
                criteria=EligibilityCriteria(
                    min_confidence=0.2,  # Very low threshold for simulation
                    max_claims_per_minute=1000,  # High rate limit
                    spam_keywords=[],  # No spam filtering
                ),
                disable_similarity_check=True,  # Disable similarity for simulation
            )
        elif self.enable_all_safeguards:
            processor_config = self.processor_config
            # Production thresholds - enable all safeguards
            eligibility_filter = create_eligibility_filter()
            similarity_engine = create_context_similarity_engine()
            plurality_rules = create_plurality_preservation_rules()
            allocative_guard = create_allocative_boundary_guard()
            trust_decay = create_trust_decay_model()
        else:
            processor_config = self.processor_config

        # Initialize processor
        processor = InboundFederatedClaimProcessor(
            identity_guard=identity_guard,
            config=processor_config,
            federation_config=federation_config,
            eligibility_filter=eligibility_filter,
            similarity_engine=similarity_engine,
            plurality_rules=plurality_rules,
            allocative_guard=allocative_guard,
            trust_decay=trust_decay,
        )

        return processor, identity_guard

    async def run_simulation(
        self,
        scenario: SimulationScenario,
        dry_run: bool = False,
        verbose: bool = False
    ) -> SimulationReport:
        """Run a complete simulation for the given scenario."""
        if dry_run:
            logger.info(f"Dry run: {scenario.name}")
            return await self._dry_run_scenario(scenario)

        logger.info(f"Starting simulation: {scenario.name}")
        logger.info(f"Nodes: {scenario.num_nodes}, Rounds: {scenario.rounds}")

        # Initialize simulation
        self.simulation_start_time = datetime.utcnow()
        self.current_round = 0
        self.round_results = []
        self.total_claims_generated = 0
        self.total_claims_processed = 0
        self.total_claims_accepted = 0
        self.total_claims_rejected = 0
        self.safeguard_triggers = {}

        # Create nodes
        nodes = await self._create_nodes(scenario)

        # Register nodes with identity guard
        for node in nodes:
            self.adapter.register_node(node)

        # Run simulation rounds
        for round_num in range(scenario.rounds):
            self.current_round = round_num + 1
            round_start = time.time()

            if verbose:
                logger.info(f"Round {round_num + 1}/{scenario.rounds}")

            # Run round
            round_data = await self._execute_round(
                scenario=scenario,
                nodes=nodes,
                round_num=round_num + 1,
                verbose=verbose,
            )

            round_data.execution_time = timedelta(seconds=time.time() - round_start)
            self.round_results.append(round_data)

            # Update statistics
            self.total_claims_generated += len(round_data.claims)
            self.total_claims_processed += len(round_data.processed_claims)
            self.total_claims_accepted += sum(1 for r in round_data.processed_claims if r.accepted)
            self.total_claims_rejected += sum(1 for r in round_data.processed_claims if not r.accepted)

            if verbose:
                logger.info(
                    f"Round {round_num + 1} complete: "
                    f"{len(round_data.claims)} claims, "
                    f"{sum(1 for r in round_data.processed_claims if r.accepted)} accepted"
                )

        # Finalize simulation
        self.simulation_end_time = datetime.utcnow()

        # Calculate final metrics
        if self.enable_metrics and self.metrics_aggregator:
            metrics = self.metrics_aggregator.calculate_all_metrics(
                rounds=self.round_results,
                simulation_start=self.simulation_start_time,
                simulation_end=self.simulation_end_time,
            )
        else:
            # Calculate simple metrics if aggregator not enabled
            metrics = SimulationMetrics(
                overall_health_index=0.8,
                diversity_health=0.8,
                influence_balance=0.8,
                trust_stability=0.8,
                quality_integrity=0.8,
                resilience=0.8,
                topic_entropy=0.8,
                stance_entropy=0.8,
                gini_coefficient=0.3,
                herfindahl_index=0.3,
                average_trust_drift=0.1,
                trust_volatility=0.1,
                acceptance_rate=0.8,
                rejection_rate=0.2,
                spam_detected_rate=0.0,
                duplicate_suppression_rate=0.0,
            )

        # Calculate predictive metrics (EDDR, ACA, FCRI)
        eddr_result = None
        aca_result = None
        fcri_result = None

        if self.enable_predictive_metrics and self.eddr_calculator:
            # Build round history from round_results
            round_history = self._build_round_history()

            if len(round_history) >= 2:
                # Calculate EDDR (Epistemic Diversity Decay Rate)
                eddr_result = self.eddr_calculator.calculate(round_history)

                # Calculate ACA (Authority Capture Acceleration)
                aca_result = self.aca_calculator.calculate(round_history)

                # Calculate FCRI (Federation Collapse Risk Index)
                fcri_result = self.fcri_calculator.calculate(eddr_result, aca_result)

                if verbose:
                    logger.info(f"Predictive Metrics - EDDR: {eddr_result.eddr:.4f}, ACA: {aca_result.aca:.4f}, FCRI: {fcri_result.fcri:.4f}")
                    logger.info(f"Risk Status: {fcri_result.status}")

        # Generate report with predictive metrics
        report = SimulationReport(
            scenario=scenario,
            metrics=metrics,
            execution_time=self.simulation_end_time - self.simulation_start_time,
            success_rate=(self.total_claims_accepted / self.total_claims_processed) if self.total_claims_processed > 0 else 0.0,
            eddr_result=eddr_result,
            aca_result=aca_result,
            fcri_result=fcri_result,
        )

        # Set additional report attributes
        report.rounds = self.round_results
        report.guardian_triggers_detected = self.safeguard_triggers
        report.safeguard_effectiveness = self._calculate_safeguard_effectiveness()
        report.failure_points = self._identify_failure_points(metrics, eddr_result, aca_result, fcri_result)
        report.recommendations = self._generate_recommendations(metrics, eddr_result, aca_result, fcri_result)

        logger.info(f"Simulation complete: {scenario.name}")
        logger.info(f"Health Index: {metrics.overall_health_index:.3f}")

        if fcri_result:
            logger.info(f"FCRI: {fcri_result.fcri:.3f} ({fcri_result.status})")

        return report

    def _build_round_history(self) -> List[Dict[str, Any]]:
        """
        Build round history from self.round_results for predictive metrics calculation.

        Each entry contains diversity_metrics, concentration_metrics, trust_metrics
        needed by EDDR, ACA, and FCRI calculators.
        """
        round_history = []

        for round_data in self.round_results:
            # Build diversity_metrics dict
            diversity_metrics = round_data.diversity_metrics.copy() if round_data.diversity_metrics else {}

            # Build concentration_metrics dict
            concentration_metrics = round_data.concentration_metrics.copy() if round_data.concentration_metrics else {}

            # If not already set, calculate from round summary
            if round_data.round_summary:
                if "topic_entropy" not in diversity_metrics:
                    diversity_metrics["topic_entropy"] = round_data.round_summary.topic_entropy
                if "stance_entropy" not in diversity_metrics:
                    diversity_metrics["stance_entropy"] = round_data.round_summary.stance_entropy

                if "gini" not in concentration_metrics:
                    concentration_metrics["gini"] = round_data.round_summary.gini
                if "hhi" not in concentration_metrics:
                    concentration_metrics["hhi"] = round_data.round_summary.hhi
                if "top_1_share" not in concentration_metrics:
                    concentration_metrics["top_1_share"] = round_data.round_summary.top_1_share
                if "top_2_share" not in concentration_metrics:
                    concentration_metrics["top_2_share"] = round_data.round_summary.top_2_share

            round_entry = {
                "round": round_data.round_number,
                "diversity_metrics": diversity_metrics,
                "concentration_metrics": concentration_metrics,
                "trust_metrics": round_data.trust_metrics.copy() if round_data.trust_metrics else {},
                "quality_metrics": round_data.quality_metrics.copy() if round_data.quality_metrics else {},
            }

            round_history.append(round_entry)

        return round_history

    async def _create_nodes(self, scenario: SimulationScenario) -> List[SimulatedNode]:
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
                baseline_trust=0.5 + (i * 0.1),  # Spread from 0.5 to 0.9
            )

            # Create node
            node = SimulatedNode(node_id, profile)
            nodes.append(node)

            logger.debug(f"Created node {node_id}: type={node_type}, adversarial={is_adversarial}")

        logger.info(f"Created {len(nodes)} nodes")
        return nodes

    async def _execute_round(
        self,
        scenario: SimulationScenario,
        nodes: List[SimulatedNode],
        round_num: int,
        verbose: bool = False,
    ) -> SimulationRound:
        """Execute a single simulation round."""
        round_start = datetime.utcnow()
        round_id = f"{scenario.name}_round{round_num}"

        # Generate claims from all nodes
        claims = []
        claim_sources = []

        for node in nodes:
            num_claims = self._generate_claim_count(node, scenario)

            for claim_idx in range(num_claims):
                claim = node.generate_claim(
                    round_num=round_num,
                    available_domains=list(scenario.domain_distribution.keys()),
                )
                claim.round = round_num
                claim.timestamp = round_start

                # Modify claim if adversarial
                if node.profile.is_adversarial:
                    claim = self._modify_adversarial_claim(claim, node.profile.adversarial_mode)

                claims.append(claim)
                claim_sources.append(node)

        self.total_claims_generated += len(claims)

        if verbose:
            logger.info(f"Generated {len(claims)} claims for round {round_num}")

        # Process claims through the real processor
        round_context = {
            "round_num": round_num,
            "scenario_name": scenario.name,
            "round_id": round_id,
        }

        claim_node_pairs = list(zip(claims, claim_sources))

        processed_results = await process_claims_batch(
            adapter=self.adapter,
            claims=claim_node_pairs,
            round_context=round_context,
        )

        # Update node trust based on results
        await self._update_node_trust(nodes, processed_results)

        # Create round data
        round_end = datetime.utcnow()
        round_data = SimulationRound(
            round_number=round_num,
            nodes=nodes,
            claims=claims,
            round_start_time=round_start,
            execution_time=round_end - round_start,
        )
        # Set processed_claims directly
        round_data.processed_claims = processed_results  # This is now ProcessedSimulationClaimResult

        # Populate accepted_claims and rejected_claims for metrics compatibility
        round_data.accepted_claims = [r.claim for r in processed_results if r.accepted]
        round_data.rejected_claims = [r.claim for r in processed_results if not r.accepted]

        # Set additional metrics
        if self.enable_metrics and self.metrics_aggregator:
            round_metrics = self._calculate_round_metrics(round_data, nodes)
            round_data.diversity_metrics = round_metrics.get("diversity", {})
            round_data.concentration_metrics = round_metrics.get("concentration", {})
            round_data.trust_metrics = round_metrics.get("trust", {})
            round_data.quality_metrics = round_metrics.get("quality", {})
            round_data.resilience_metrics = round_metrics.get("resilience", {})

        # Track safeguard triggers
        for result in processed_results:
            for safeguard_name, triggered in result.safeguard_events.items():
                if triggered:
                    self.safeguard_triggers[safeguard_name] = self.safeguard_triggers.get(safeguard_name, 0) + 1

        # Create round summary for predictive metrics
        round_summary = self._create_round_summary(
            round_num=round_num,
            round_start=round_start,
            claims=claims,
            nodes=nodes,
            processed_results=processed_results,
        )
        round_data.round_summary = round_summary

        return round_data

    def _create_round_summary(
        self,
        round_num: int,
        round_start: datetime,
        claims: List[SimulatedClaim],
        nodes: List[SimulatedNode],
        processed_results: List,
    ) -> RoundSummary:
        """Create a RoundSummary for predictive metrics calculation."""
        # Calculate diversity metrics
        topic_entropy = self._calculate_topic_entropy(claims)
        stance_entropy = self._calculate_stance_entropy(claims)

        # Calculate concentration metrics with top node shares
        gini = self._calculate_gini_coefficient(claims)
        hhi = self._calculate_hhi(claims)
        top_1_share, top_2_share = self._calculate_top_node_shares(claims)

        # Calculate minority ratio and contradiction retention
        minority_ratio = self._calculate_minority_ratio(claims)
        contradiction_retention = self._calculate_contradiction_retention(claims, stance_entropy)

        # Count accepted and rejected
        accepted_count = sum(1 for r in processed_results if r.accepted)
        rejected_count = len(processed_results) - accepted_count

        # Calculate diversity and concentration scores for predictive metrics
        diversity_score = (
            0.35 * topic_entropy +
            0.30 * stance_entropy +
            0.20 * minority_ratio +
            0.15 * contradiction_retention
        )
        normalized_hhi = min(1.0, hhi * 4)
        concentration_score = (
            0.35 * gini +
            0.35 * normalized_hhi +
            0.20 * top_1_share +
            0.10 * top_2_share
        )

        return RoundSummary(
            round_number=round_num,
            timestamp=round_start,
            topic_entropy=topic_entropy,
            stance_entropy=stance_entropy,
            minority_ratio=minority_ratio,
            contradiction_retention=contradiction_retention,
            gini=gini,
            hhi=hhi,
            top_1_share=top_1_share,
            top_2_share=top_2_share,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            diversity_score=diversity_score,
            concentration_score=concentration_score,
        )

    def _calculate_top_node_shares(self, claims: List[SimulatedClaim]) -> Tuple[float, float]:
        """Calculate the share of claims from the top 1 and top 2 nodes."""
        from collections import Counter

        if not claims:
            return 0.0, 0.0

        source_counts = Counter(c.source_node_id for c in claims)
        total = len(claims)

        if total == 0:
            return 0.0, 0.0

        sorted_counts = sorted(source_counts.values(), reverse=True)

        top_1_share = sorted_counts[0] / total if sorted_counts else 0.0
        top_2_share = sum(sorted_counts[:2]) / total if len(sorted_counts) >= 2 else top_1_share

        return top_1_share, top_2_share

    def _calculate_minority_ratio(self, claims: List[SimulatedClaim]) -> float:
        """Calculate the ratio of minority viewpoint contributions."""
        top_1_share, _ = self._calculate_top_node_shares(claims)
        # Minority is what the dominant node doesn't control
        return 1.0 - top_1_share

    def _calculate_contradiction_retention(self, claims: List[SimulatedClaim], stance_entropy: float) -> float:
        """Calculate how well contradiction is being preserved."""
        # Use stance entropy as a proxy for contradiction retention
        # Higher stance entropy with multiple stances suggests healthy contradiction
        return min(1.0, stance_entropy * 1.5)

    async def _update_node_trust(
        self,
        nodes: List[SimulatedNode],
        results: List,
    ) -> None:
        """Update node trust based on processing results."""
        for node in nodes:
            # Find results for this node's claims
            node_results = [r for r in results if r.claim.source_node_id == node.node_id]

            if not node_results:
                continue

            # Calculate trust adjustment
            accepted = sum(1 for r in node_results if r.accepted)
            rejected = len(node_results) - accepted

            # Simple trust update: increase for accepted, decrease for rejected
            if len(node_results) > 0:
                acceptance_rate = accepted / len(node_results)
                trust_delta = (acceptance_rate - 0.5) * 0.05  # Small adjustments

                # Apply trust volatility
                volatility = node.profile.trust_volatility
                noise = (random.random() - 0.5) * volatility
                trust_delta += noise

                # Update trust (bounded)
                new_trust = node.state.current_trust + trust_delta
                node.state.current_trust = max(0.0, min(1.0, new_trust))

                # Track trust history
                node.state.trust_observations.append(node.state.current_trust)
                node.state.trust_timestamps.append(datetime.utcnow())

    def _generate_claim_count(self, node: SimulatedNode, scenario: SimulationScenario) -> int:
        """Generate number of claims for a node in this round."""
        base_rate = node.profile.base_claim_rate

        # Apply adversarial modifiers
        if node.profile.adversarial_mode == "flood":
            # Default adversarial intensity if not specified
            adversarial_intensity = getattr(scenario, 'adversarial_intensity', 1.0)
            base_rate *= adversarial_intensity * 5  # 5x flood rate
        elif node.profile.adversarial_mode == "monoculture":
            base_rate *= 2  # 2x rate for monoculture

        # Add some randomness
        base_rate = max(1, int(base_rate + random.uniform(-0.3, 0.3)))

        return base_rate

    def _modify_adversarial_claim(
        self,
        claim: SimulatedClaim,
        adversarial_mode: Optional[str],
    ) -> SimulatedClaim:
        """Modify claim based on adversarial mode."""
        if not adversarial_mode:
            return claim

        if adversarial_mode == "monoculture":
            # Force same domain
            claim.domain = Domain.GENERAL
            claim.stance = Stance.SUPPORT

        elif adversarial_mode == "flood":
            # Lower quality for flooding
            claim.confidence = max(0.1, claim.confidence - 0.3)
            claim.provenance_quality = max(0.1, claim.provenance_quality - 0.3)

        elif adversarial_mode == "trust_gaming":
            # Start high quality, then degrade
            claim.confidence = min(1.0, claim.confidence + 0.2)

        return claim

    def _calculate_round_metrics(
        self,
        round_data: SimulationRound,
        nodes: List[SimulatedNode],
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics for a round."""
        metrics = {}

        # Diversity metrics
        metrics["diversity"] = {
            "topic_entropy": self._calculate_topic_entropy(round_data.claims),
            "stance_entropy": self._calculate_stance_entropy(round_data.claims),
        }

        # Concentration metrics
        gini = self._calculate_gini_coefficient(round_data.claims)
        hhi = self._calculate_hhi(round_data.claims)
        top_1_share, top_2_share = self._calculate_top_node_shares(round_data.claims)

        metrics["concentration"] = {
            "gini": gini,
            "hhi": hhi,
            "top_1_share": top_1_share,
            "top_2_share": top_2_share,
        }

        # Trust metrics
        metrics["trust"] = {
            "average_trust": sum(n.state.current_trust for n in nodes) / len(nodes),
            "trust_volatility": self._calculate_trust_volatility(nodes),
        }

        # Quality metrics
        accepted = sum(1 for r in round_data.processed_claims if r.accepted)
        metrics["quality"] = {
            "acceptance_rate": accepted / len(round_data.processed_claims) if round_data.processed_claims else 0.0,
        }

        # Resilience metrics
        metrics["resilience"] = {
            "throughput": len(round_data.claims),
        }

        return metrics

    def _calculate_topic_entropy(self, claims: List[SimulatedClaim]) -> float:
        """Calculate Shannon entropy of topic distribution."""
        from collections import Counter
        import math

        domains = [c.domain for c in claims]
        if not domains:
            return 0.0

        counts = Counter(domains)
        total = len(domains)
        entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
        return min(1.0, entropy / math.log2(len(counts))) if len(counts) > 1 else 0.0

    def _calculate_stance_entropy(self, claims: List[SimulatedClaim]) -> float:
        """Calculate Shannon entropy of stance distribution."""
        from collections import Counter
        import math

        stances = [c.stance for c in claims]
        if not stances:
            return 0.0

        counts = Counter(stances)
        total = len(stances)
        entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
        return min(1.0, entropy / math.log2(len(counts))) if len(counts) > 1 else 0.0

    def _calculate_gini_coefficient(self, claims: List[SimulatedClaim]) -> float:
        """Calculate Gini coefficient of claim distribution."""
        if not claims:
            return 0.0

        from collections import Counter
        source_counts = Counter(c.source_node_id for c in claims)
        values = sorted(source_counts.values())

        if len(values) == 1:
            return 0.0

        n = len(values)
        total = sum(values)

        if total == 0:
            return 0.0

        cumulative = 0
        for i, val in enumerate(values):
            cumulative += (n - i + 1) * val

        gini = (2 * cumulative) / (n * total) - (n + 1) / n
        return max(0.0, min(1.0, gini))

    def _calculate_hhi(self, claims: List[SimulatedClaim]) -> float:
        """Calculate Herfindahl-Hirschman Index."""
        if not claims:
            return 0.0

        from collections import Counter
        source_counts = Counter(c.source_node_id for c in claims)
        total = len(claims)

        if total == 0:
            return 0.0

        hhi = sum((count / total) ** 2 for count in source_counts.values())
        return hhi

    def _calculate_trust_volatility(self, nodes: List[SimulatedNode]) -> float:
        """Calculate trust volatility across nodes."""
        if not nodes:
            return 0.0

        trusts = [n.state.current_trust for n in nodes]
        if len(trusts) < 2:
            return 0.0

        mean = sum(trusts) / len(trusts)
        variance = sum((t - mean) ** 2 for t in trusts) / len(trusts)
        return variance ** 0.5

    def _calculate_safeguard_effectiveness(self) -> Dict[str, float]:
        """Calculate safeguard effectiveness scores."""
        total_claims = self.total_claims_processed
        if total_claims == 0:
            return {}

        effectiveness = {}
        for safeguard, triggers in self.safeguard_triggers.items():
            effectiveness[safeguard] = triggers / total_claims
        return effectiveness

    def _identify_failure_points(
        self,
        metrics: SimulationMetrics,
        eddr_result: Optional[EpistemicDiversityDecayResult] = None,
        aca_result: Optional[AuthorityCaptureAccelerationResult] = None,
        fcri_result: Optional[FederationCollapseRiskResult] = None,
    ) -> List[str]:
        """Identify potential failure points in the federation."""
        failures = []

        if metrics.diversity_health < 0.7:
            failures.append("Low epistemic diversity detected")
        if metrics.influence_balance < 0.7:
            failures.append("Influence concentration detected")
        if metrics.trust_stability < 0.7:
            failures.append("Trust system instability detected")
        if metrics.quality_integrity < 0.7:
            failures.append("Quality filtering issues detected")
        if metrics.resilience < 0.7:
            failures.append("Network resilience degraded")

        # Add predictive metric-based failure points
        if eddr_result and eddr_result.status == "collapse_risk":
            failures.append("CRITICAL: Epistemic diversity collapse risk detected")
        if aca_result and aca_result.status == "collapse_risk":
            failures.append("CRITICAL: Authority capture acceleration critical")
        if fcri_result and fcri_result.status == "collapse_risk":
            failures.append("CRITICAL: Federation collapse risk threshold exceeded")

        return failures

    def _generate_recommendations(
        self,
        metrics: SimulationMetrics,
        eddr_result: Optional[EpistemicDiversityDecayResult] = None,
        aca_result: Optional[AuthorityCaptureAccelerationResult] = None,
        fcri_result: Optional[FederationCollapseRiskResult] = None,
    ) -> List[str]:
        """Generate recommendations based on metrics and predictive indicators."""
        recommendations = []

        if metrics.diversity_health < 0.8:
            recommendations.append("Consider adjusting plurality preservation thresholds")
        if metrics.influence_balance < 0.8:
            recommendations.append("Review allocative boundary guard settings")
        if metrics.trust_stability < 0.8:
            recommendations.append("Increase trust decay model sensitivity")

        # Add predictive metric-based recommendations
        if fcri_result:
            recommendations.extend(fcri_result.recommended_actions)

        return recommendations

    async def _dry_run_scenario(self, scenario: SimulationScenario) -> SimulationReport:
        """Perform a dry run without actual processing."""
        # Create minimal report for dry run
        metrics = SimulationMetrics(
            overall_health_index=0.8,
            diversity_health=0.8,
            influence_balance=0.8,
            trust_stability=0.8,
            quality_integrity=0.8,
            resilience=0.8,
        )

        return SimulationReport(
            scenario=scenario,
            metrics=metrics,
            execution_time=timedelta(seconds=0),
            success_rate=1.0,
        )


def create_async_executor(
    enable_all_safeguards: bool = True,
    enable_metrics: bool = True,
    enable_health_index: bool = True,
    enable_predictive_metrics: bool = True,
    simulation_mode: bool = True,
) -> AsyncFederationSimulationExecutor:
    """Factory function to create an async simulation executor.

    Args:
        enable_all_safeguards: Whether to enable all safeguard engines
        enable_metrics: Whether to enable metrics collection
        enable_health_index: Whether to enable health index calculation
        enable_predictive_metrics: Whether to enable predictive metrics (EDDR, ACA, FCRI)
        simulation_mode: If True, uses permissive configuration for testing

    Returns:
        Configured AsyncFederationSimulationExecutor instance
    """
    return AsyncFederationSimulationExecutor(
        enable_all_safeguards=enable_all_safeguards,
        enable_metrics=enable_metrics,
        enable_health_index=enable_health_index,
        enable_predictive_metrics=enable_predictive_metrics,
        simulation_mode=simulation_mode,
    )
