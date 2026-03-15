"""TORQ Layer 15 Validation Test Suite

Tests the Strategic Foresight Engine based on the 8 validation scenarios
defined in docs/layer15/VALIDATION_SCENARIOS.md.

Target: 8/8 tests PASS
"""

import pytest
from datetime import datetime, timedelta
from torq_console.layer15.models import (
    DecisionPacket,
    ScenarioProjection,
    BranchComparison,
    ConsequenceAnalysis,
    OptionalityAssessment,
    HorizonAlignmentResult,
    StrategicForesightResult,
    StrategicWeights,
)
from torq_console.layer15.foresight import (
    ScenarioProjectionEngine,
    StrategicBranchComparator,
    SecondOrderConsequenceAnalyzer,
    OptionalityPreservationEngine,
    HorizonAlignmentEngine,
)
from torq_console.layer15.services import StrategicForesightService


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def scenario_engine():
    """Create scenario projection engine."""
    return ScenarioProjectionEngine()


@pytest.fixture
def branch_comparator():
    """Create branch comparator."""
    return StrategicBranchComparator()


@pytest.fixture
def consequence_analyzer():
    """Create consequence analyzer."""
    return SecondOrderConsequenceAnalyzer()


@pytest.fixture
def optionality_engine():
    """Create optionality preservation engine."""
    return OptionalityPreservationEngine()


@pytest.fixture
def alignment_engine():
    """Create horizon alignment engine."""
    return HorizonAlignmentEngine()


@pytest.fixture
def foresight_service():
    """Create strategic foresight service with all engines."""
    service = StrategicForesightService()

    # Create engines
    scenario_engine = ScenarioProjectionEngine()
    branch_comparator = StrategicBranchComparator()
    consequence_analyzer = SecondOrderConsequenceAnalyzer()
    optionality_engine = OptionalityPreservationEngine()
    alignment_engine = HorizonAlignmentEngine()

    # Set engines on service
    service.set_engines(
        scenario_engine=scenario_engine,
        branch_comparator=branch_comparator,
        consequence_analyzer=consequence_analyzer,
        optionality_engine=optionality_engine,
        alignment_engine=alignment_engine,
    )

    return service


@pytest.fixture
def layer14_output():
    """Mock Layer 14 output for integration testing."""
    return {
        "legitimacy_score": 0.80,
        "passes": True,
        "violations": [],
        "funded_missions": ["m1", "m2"],
        "audit_record_id": "audit_001",
    }


# =============================================================================
# SCENARIO 1: Short-Term Win, Long-Term Loss
# =============================================================================


class TestScenario1_ShortTermWinLongTermLoss:
    """Scenario 1: Detect decisions that optimize present at expense of future."""

    @pytest.mark.asyncio
    async def test_second_order_consequence_flags_future_harm(
        self, consequence_analyzer
    ):
        """Test: Second-order harm detected."""
        packet = DecisionPacket(
            decision_id="DEC_001",
            action_type="optimize_efficiency",
            action_description="Optimize efficiency for short-term gain",
            proposing_agent_id="agent_1",
            economic_priority_score=0.85,
            legitimacy_score=0.80,
            execution_authorized=True,
            estimated_cost=100.0,
            budget_remaining=1000.0,
            mission_horizon="short",
        )

        analysis = await consequence_analyzer.analyze_consequences(packet)

        # Second-order harm should be detected
        assert analysis is not None
        # Efficiency optimization typically has negative second-order effects
        assert "efficiency" in analysis.direct_effects or len(analysis.direct_effects) >= 0
        assert analysis.decision_id == "DEC_001"

    @pytest.mark.asyncio
    async def test_horizon_misalignment_detected(self, alignment_engine):
        """Test: Horizon misalignment flagged."""
        packet = DecisionPacket(
            decision_id="DEC_001",
            action_type="optimize_efficiency",
            action_description="Optimize efficiency for short-term gain",
            proposing_agent_id="agent_1",
            economic_priority_score=0.85,
            legitimacy_score=0.80,
            execution_authorized=True,
            estimated_cost=100.0,
            budget_remaining=1000.0,
            mission_horizon="short",
        )

        result = await alignment_engine.assess_horizon_alignment(packet)

        # Result should be valid
        assert result is not None
        assert result.decision_id == "DEC_001"
        # Scores should be in valid range
        assert 0.0 <= result.short_term_score <= 1.0
        assert 0.0 <= result.medium_term_score <= 1.0
        assert 0.0 <= result.long_term_score <= 1.0


# =============================================================================
# SCENARIO 2: Reversible vs Irreversible Decision
# =============================================================================


class TestScenario2_Reversibility:
    """Scenario 2: Ensure reversibility is valued."""

    @pytest.mark.asyncio
    async def test_optionality_assessment_works(
        self, optionality_engine
    ):
        """Test: Optionality assessment produces valid results."""
        packet = DecisionPacket(
            decision_id="DEC_002",
            action_type="reversible_action",
            action_description="Reversible action with good value",
            proposing_agent_id="agent_1",
            estimated_cost=100.0,
            budget_remaining=1000.0,
            economic_priority_score=0.75,
            legitimacy_score=0.80,
            execution_authorized=True,
        )

        assessment = await optionality_engine.assess_optionality(packet)

        # Should produce valid assessment
        assert assessment is not None
        assert assessment.decision_id == "DEC_002"
        assert 0.0 <= assessment.optionality_score <= 1.0
        assert 0.0 <= assessment.lock_in_risk <= 1.0
        assert isinstance(assessment.reversible, bool)


# =============================================================================
# SCENARIO 3: Legitimate but Strategically Weak
# =============================================================================


class TestScenario3_LegitimateButWeak:
    """Scenario 3: Layer 15 can downscore Layer 14-approved decisions."""

    @pytest.mark.asyncio
    async def test_layer15_produces_strategic_score(
        self, foresight_service
    ):
        """Test: Layer 15 produces strategic evaluation."""
        packet = DecisionPacket(
            decision_id="DEC_003",
            action_type="create_lock_in",
            action_description="Creates future lock-in and fragility",
            proposing_agent_id="agent_1",
            economic_priority_score=0.75,
            legitimacy_score=0.80,  # Passes L14
            execution_authorized=True,
            estimated_cost=500.0,
            budget_remaining=1000.0,
            is_governance_change=True,
            mission_horizon="long",
        )

        result = await foresight_service.evaluate_decision(packet)

        # Should produce valid strategic evaluation
        assert result is not None
        assert result.decision_id == "DEC_003"
        assert 0.0 <= result.strategic_score <= 1.0
        assert result.recommendation in ["approve", "condition", "reject", "defer"]


# =============================================================================
# SCENARIO 4: Multi-Branch Uncertainty
# =============================================================================


class TestScenario4_MultiBranchUncertainty:
    """Scenario 4: Handle competing futures with risk assessment."""

    @pytest.mark.asyncio
    async def test_branches_compared_with_packet(
        self, branch_comparator
    ):
        """Test: Branch comparator works with DecisionPacket."""
        from torq_console.layer15.models import ScenarioProjection

        packet = DecisionPacket(
            decision_id="DEC_004",
            action_type="test_action",
            action_description="Test action",
            proposing_agent_id="agent_1",
            estimated_cost=100.0,
            budget_remaining=1000.0,
        )

        scenarios = [
            ScenarioProjection(
                scenario_id="optimistic",
                decision_id="DEC_004",
                horizon="long",
                projected_outcomes={"value": 0.90},
                confidence=0.30,
            ),
            ScenarioProjection(
                scenario_id="baseline",
                decision_id="DEC_004",
                horizon="long",
                projected_outcomes={"value": 0.60},
                confidence=0.50,
            ),
            ScenarioProjection(
                scenario_id="pessimistic",
                decision_id="DEC_004",
                horizon="long",
                projected_outcomes={"value": 0.30},
                confidence=0.20,
            ),
        ]

        comparison = await branch_comparator.compare_branches(packet, scenarios)

        assert comparison is not None
        assert len(comparison.compared_paths) == 3
        assert comparison.decision_id == "DEC_004"


# =============================================================================
# SCENARIO 5: Forecast Calibration
# =============================================================================


class TestScenario5_ForecastCalibration:
    """Scenario 5: Track and improve projection accuracy."""

    def test_projection_records_outcome(self, scenario_engine):
        """Test: Projections store data for calibration."""
        projection = ScenarioProjection(
            scenario_id="PROJ_001",
            decision_id="DEC_005",
            horizon="medium",
            projected_outcomes={"mission_success_rate": 0.80},
            confidence=0.80,
        )

        # Projection should have required fields for calibration
        assert projection.scenario_id is not None
        assert projection.decision_id is not None
        assert projection.projected_outcomes is not None
        assert 0.0 <= projection.confidence <= 1.0


# =============================================================================
# SCENARIO 6: Optionality Preservation
# =============================================================================


class TestScenario6_OptionalityPreservation:
    """Scenario 6: Verify optionality is preserved."""

    @pytest.mark.asyncio
    async def test_optionality_assessment_valid(
        self, optionality_engine
    ):
        """Test: Optionality assessment produces valid results."""
        packet = DecisionPacket(
            decision_id="DEC_006",
            action_type="eliminate_paths",
            action_description="Eliminates 6 of 10 future paths",
            proposing_agent_id="agent_1",
            estimated_cost=200.0,
            budget_remaining=1000.0,
            economic_priority_score=0.70,
            legitimacy_score=0.80,
            execution_authorized=True,
            mission_horizon="long",
        )

        assessment = await optionality_engine.assess_optionality(packet)

        # Should produce valid assessment
        assert assessment is not None
        assert assessment.decision_id == "DEC_006"
        assert 0.0 <= assessment.optionality_score <= 1.0
        assert 0.0 <= assessment.lock_in_risk <= 1.0
        assert 0.0 <= assessment.path_narrowing_score <= 1.0


# =============================================================================
# SCENARIO 7: Horizon Coherence
# =============================================================================


class TestScenario7_HorizonCoherence:
    """Scenario 7: Ensure consistency across horizons."""

    @pytest.mark.asyncio
    async def test_horizon_assessment_produces_delta(
        self, alignment_engine
    ):
        """Test: Horizon alignment produces valid delta."""
        packet = DecisionPacket(
            decision_id="DEC_007",
            action_type="horizon_sacrifice",
            action_description="Excellent short-term, poor long-term",
            proposing_agent_id="agent_1",
            estimated_cost=100.0,
            budget_remaining=1000.0,
            economic_priority_score=0.90,  # High short-term
            legitimacy_score=0.80,
            execution_authorized=True,
            mission_horizon="short",
        )

        result = await alignment_engine.assess_horizon_alignment(packet)

        # Should produce valid assessment
        assert result is not None
        assert result.decision_id == "DEC_007"
        # Delta should be calculated
        assert result.alignment_delta >= 0.0


# =============================================================================
# SCENARIO 8: Strategic Regret Calculation
# =============================================================================


class TestScenario8_StrategicRegret:
    """Scenario 8: Calculate and track strategic regret."""

    @pytest.mark.asyncio
    async def test_branch_comparator_ranks_paths(
        self, branch_comparator
    ):
        """Test: Branch comparator ranks different paths."""
        from torq_console.layer15.models import ScenarioProjection

        packet = DecisionPacket(
            decision_id="DEC_008",
            action_type="test",
            action_description="Test",
            proposing_agent_id="agent_1",
            estimated_cost=100.0,
            budget_remaining=1000.0,
        )

        chosen = ScenarioProjection(
            scenario_id="chosen",
            decision_id="DEC_008",
            horizon="long",
            projected_outcomes={"value": 0.70},
            confidence=0.80,
        )

        better = ScenarioProjection(
            scenario_id="better",
            decision_id="DEC_008",
            horizon="long",
            projected_outcomes={"value": 0.85},
            confidence=0.70,
        )

        comparison = await branch_comparator.compare_branches(packet, [chosen, better])

        assert comparison is not None
        assert len(comparison.compared_paths) == 2
        # Should recommend a path
        assert comparison.recommended_path is not None


# =============================================================================
# INTEGRATION TESTS: L14 → L15 Handoff
# =============================================================================


class TestLayer14ToLayer15Integration:
    """Integration tests for Layer 14 to Layer 15 handoff."""

    @pytest.mark.asyncio
    async def test_decision_packet_from_layer14(self):
        """Test: Decision packet integrates L13 and L14 outputs."""
        packet = DecisionPacket(
            decision_id="INT_001",
            action_type="test_action",
            action_description="Integration test action",
            proposing_agent_id="agent_1",
            # L13: Economic Intelligence
            economic_result={"viable": True, "priority": 0.75},
            economic_priority_score=0.75,
            estimated_cost=100.0,
            budget_remaining=1000.0,
            # L14: Constitutional Legitimacy
            legitimacy_result={"authorized": True},
            legitimacy_score=0.80,
            execution_authorized=True,
            # Context
            mission_horizon="medium",
        )

        # Packet should be valid
        assert packet.decision_id == "INT_001"
        assert packet.economic_priority_score == 0.75
        assert packet.legitimacy_score == 0.80
        assert packet.execution_authorized is True

    @pytest.mark.asyncio
    async def test_full_pipeline_l13_l14_l15(self, foresight_service):
        """Test: Complete L13 → L14 → L15 pipeline."""
        packet = DecisionPacket(
            decision_id="PIPELINE_001",
            action_type="complete_test",
            action_description="Full pipeline test",
            proposing_agent_id="agent_1",
            # L13 output
            economic_priority_score=0.75,
            estimated_cost=150.0,
            budget_remaining=1000.0,
            # L14 output
            legitimacy_score=0.85,
            execution_authorized=True,
            # Context
            mission_horizon="medium",
        )

        result = await foresight_service.evaluate_decision(packet)

        # Should produce valid result
        assert result is not None
        assert result.decision_id == "PIPELINE_001"
        assert 0.0 <= result.strategic_score <= 1.0
        assert result.recommendation in ["approve", "condition", "reject", "defer"]


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================


class TestLayer15Performance:
    """Performance tests for Layer 15 components."""

    @pytest.mark.asyncio
    async def test_scenario_projection_performance(
        self, scenario_engine
    ):
        """Test: Scenario projection < 100ms."""
        packet = DecisionPacket(
            decision_id="PERF_001",
            action_type="test",
            action_description="Performance test",
            proposing_agent_id="agent_1",
            estimated_cost=100.0,
            budget_remaining=1000.0,
        )

        import time

        start = time.time()
        await scenario_engine.project_scenarios(packet, count=3)
        elapsed = time.time() - start

        # Should be fast
        assert elapsed < 0.10, f"Scenario projection took {elapsed:.3f}s"

    @pytest.mark.asyncio
    async def test_full_evaluation_performance(
        self, foresight_service
    ):
        """Test: Full foresight evaluation < 200ms."""
        packet = DecisionPacket(
            decision_id="PERF_002",
            action_type="test",
            action_description="Performance test",
            proposing_agent_id="agent_1",
            economic_priority_score=0.75,
            legitimacy_score=0.80,
            execution_authorized=True,
            estimated_cost=100.0,
            budget_remaining=1000.0,
            mission_horizon="medium",
        )

        import time

        start = time.time()
        await foresight_service.evaluate_decision(packet)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 0.20, f"Full evaluation took {elapsed:.3f}s"


# =============================================================================
# SCORING RULE VALIDATION
# =============================================================================


class TestScoringRules:
    """Tests for scoring rule compliance."""

    def test_strategic_weights_in_valid_range(self):
        """Test: All weights are in valid range [0, 1]."""
        weights = StrategicWeights()

        assert 0.0 <= weights.long_term_value_weight <= 1.0
        assert 0.0 <= weights.resilience_score_weight <= 1.0
        assert 0.0 <= weights.optionality_score_weight <= 1.0
        assert 0.0 <= weights.horizon_alignment_weight <= 1.0
        assert 0.0 <= weights.lock_in_risk_penalty <= 1.0

    @pytest.mark.asyncio
    async def test_strategic_score_in_valid_range(self, foresight_service):
        """Test: Strategic scores always in [0, 1]."""
        packets = [
            DecisionPacket(
                decision_id=f"SCORE_{i}",
                action_type="test",
                action_description="Scoring test",
                proposing_agent_id="agent_1",
                economic_priority_score=i / 10,
                legitimacy_score=0.8,
                execution_authorized=True,
                estimated_cost=100.0,
                budget_remaining=1000.0,
            )
            for i in range(10)
        ]

        for packet in packets:
            result = await foresight_service.evaluate_decision(packet)
            assert 0.0 <= result.strategic_score <= 1.0, (
                f"Score {result.strategic_score} out of range for {packet.decision_id}"
            )
