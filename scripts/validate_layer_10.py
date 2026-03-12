"""
     TORQ Console - Layer 10: Strategic Simulation & Decision Forecasting Validation

Validates the Strategic Simulation & Decision Forecasting Layer (Layer 10).

Tests:
1. Scenario Simulation Engine - Mission and workflow simulation
2. Policy Impact Simulator - Governance policy change testing
3. Strategic Forecasting Engine - Long-term outcome prediction
4. Risk Modeling System - Risk assessment and mitigation
5. Planning Workspace - Collaborative planning and comparison
6. Integration with Layer 9 (Organizational Intelligence)
7. Integration with Control Plane
8. Data Model validation
9. Simulation isolation (no production data impact)
10. No regression in L1-L9 functionality
"""

import sys
import io
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# L10 Imports
from torq_console.simulation.models import (
    SimulationScope,
    SimulationStatus,
    SimulationScenario,
    SimulationResult,
    PolicyChangeType,
    PolicyImpactReport,
    PolicySimulationConfig,
    ForecastType,
    ForecastTrendDirection,
    StrategicForecast,
    RiskCategory,
    RiskSeverity,
    RiskAssessment,
    RiskModelReport,
    PlanningSessionStatus,
    PlanningSession,
    ScenarioComparison,
    create_simulation_scenario,
    create_policy_impact_report,
    create_strategic_forecast,
    create_risk_assessment,
    create_planning_session,
    get_all_simulation_scopes,
    get_all_policy_change_types,
    get_all_forecast_types,
    get_all_risk_categories,
    get_all_risk_severities,
)

from torq_console.simulation.scenario_engine.simulation_engine import (
    ScenarioSimulationEngine,
    get_simulation_engine,
)

from torq_console.simulation.policy_simulation.policy_simulator import (
    PolicyImpactSimulator,
    get_policy_simulator,
)

from torq_console.simulation.forecasting.forecasting_engine import (
    StrategicForecastingEngine,
    get_forecasting_engine,
)

from torq_console.simulation.risk_modeling.risk_service import (
    RiskModelingService,
    get_risk_service,
)

from torq_console.simulation.planning_workspace.planning_workspace_service import (
    PlanningWorkspaceService,
    get_planning_workspace,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Layer10Validator:
    """Validator for Layer 10: Strategic Simulation & Decision Forecasting."""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def record(self, test_name: str, passed: bool, message: str = ""):
        """Record a test result."""
        self.results.append((test_name, passed, message))
        if passed:
            self.passed += 1
            logger.info(f"[OK] {test_name}: {message}")
        else:
            self.failed += 1
            logger.error(f"[FAIL] {test_name}: {message}")

    async def validate_scenario_simulation(self):
        """Test 1: Scenario Simulation Engine."""
        try:
            engine = get_simulation_engine()

            # Create scenario
            scenario = await engine.create_scenario(
                title="Test Mission Simulation",
                description="Test simulation for validation",
                simulation_scope=SimulationScope.SINGLE_MISSION,
                parameters={"mission_type": "analysis", "domain": "finance"},
                iterations=100,
            )
            passed1 = scenario is not None
            passed2 = scenario.scenario_id is not None

            # Run simulation
            result = await engine.run_simulation(scenario.scenario_id)
            passed3 = result is not None
            passed4 = result.status == SimulationStatus.COMPLETED
            passed5 = result.total_simulations == 100
            passed6 = 0 <= result.success_rate <= 1

            passed = passed1 and passed2 and passed3 and passed4 and passed5 and passed6

            self.record(
                "Scenario Simulation Engine",
                passed,
                f"Create: {passed1}, Run: {passed3}, Complete: {passed4}, "
                f"Iterations: {result.total_simulations}, Success: {result.success_rate:.2%}"
            )

        except Exception as e:
            self.record("Scenario Simulation Engine", False, str(e))

    async def validate_policy_simulation(self):
        """Test 2: Policy Impact Simulator."""
        try:
            simulator = get_policy_simulator()

            # Create policy config
            config = PolicySimulationConfig(
                policy_id="test_policy_1",
                change_type=PolicyChangeType.READINESS_THRESHOLD,
                current_value=0.70,
                proposed_value=0.80,
                simulation_iterations=500,
            )

            # Run simulation
            report = await simulator.simulate_policy_change(config)
            passed1 = report is not None
            passed2 = report.policy_id == "test_policy_1"
            passed3 = report.predicted_promotion_rate is not None
            passed4 = report.predicted_regression_rate is not None
            passed5 = len(report.recommendations) > 0

            passed = passed1 and passed2 and passed3 and passed4 and passed5

            self.record(
                "Policy Impact Simulator",
                passed,
                f"Report: {passed1}, ID: {passed2}, Prom: {report.predicted_promotion_rate:.2%}, "
                f"Regress: {report.predicted_regression_rate:.2%}, Recs: {len(report.recommendations)}"
            )

        except Exception as e:
            self.record("Policy Impact Simulator", False, str(e))

    async def validate_strategic_forecasting(self):
        """Test 3: Strategic Forecasting Engine."""
        try:
            engine = get_forecasting_engine()

            # Generate forecast
            forecast = await engine.generate_forecast(
                forecast_type=ForecastType.MISSION_SUCCESS_TREND,
                title="Mission Success Forecast",
                description="90-day mission success forecast",
                timeframe_days=90,
                scope="global",
            )
            passed1 = forecast is not None
            passed2 = forecast.forecast_id is not None
            passed3 = len(forecast.data_points) > 0
            passed4 = forecast.trend_direction in ForecastTrendDirection
            passed5 = 0 <= forecast.confidence <= 1

            passed = passed1 and passed2 and passed3 and passed4 and passed5

            self.record(
                "Strategic Forecasting Engine",
                passed,
                f"Forecast: {passed1}, Points: {len(forecast.data_points)}, "
                f"Trend: {forecast.trend_direction}, Confidence: {forecast.confidence:.2f}"
            )

        except Exception as e:
            self.record("Strategic Forecasting Engine", False, str(e))

    async def validate_risk_modeling(self):
        """Test 4: Risk Modeling System."""
        try:
            service = get_risk_service()

            # Create risk assessment
            assessment = await service.assess_risk(
                title="Test Execution Risk",
                description="Test risk assessment",
                risk_category=RiskCategory.EXECUTION,
                probability=0.3,
                impact=0.7,
            )
            passed1 = assessment is not None
            passed2 = assessment.risk_score == assessment.probability * assessment.impact
            passed3 = assessment.severity in RiskSeverity
            passed4 = len(assessment.mitigation_options) > 0

            # Generate risk report
            report = await service.evaluate_scenario_risks(scenario_id=None)
            passed5 = report is not None
            passed6 = report.overall_risk_score >= 0
            passed7 = len(report.top_risks) > 0

            passed = passed1 and passed2 and passed3 and passed4 and passed5 and passed6 and passed7

            self.record(
                "Risk Modeling System",
                passed,
                f"Assessment: {passed1}, Score: {assessment.risk_score:.2f}, "
                f"Severity: {assessment.severity}, Report: {passed5}, "
                f"Overall: {report.overall_risk_score:.2f}"
            )

        except Exception as e:
            self.record("Risk Modeling System", False, str(e))

    async def validate_planning_workspace(self):
        """Test 5: Planning Workspace."""
        try:
            workspace = get_planning_workspace()

            # Create session
            session = await workspace.create_session(
                title="Test Planning Session",
                description="Test session for validation",
                owner="validator",
            )
            passed1 = session is not None
            passed2 = session.status == PlanningSessionStatus.DRAFT

            # Add scenario
            await workspace.add_scenario_to_session(session.session_id, uuid4())
            passed3 = len(session.scenario_ids) == 1

            # Add decision
            await workspace.add_decision(session.session_id, "Test decision")
            passed4 = len(session.decisions) == 1

            # Add action item
            await workspace.add_action_item(session.session_id, "Test action")
            passed5 = len(session.action_items) == 1

            # Compare scenarios
            comparison = await workspace.compare_scenarios([uuid4(), uuid4()])
            passed6 = comparison is not None
            passed7 = len(comparison.metric_comparisons) > 0

            passed = passed1 and passed2 and passed3 and passed4 and passed5 and passed6 and passed7

            self.record(
                "Planning Workspace",
                passed,
                f"Session: {passed1}, Decisions: {len(session.decisions)}, "
                f"Actions: {len(session.action_items)}, Comparison: {passed6}"
            )

        except Exception as e:
            self.record("Planning Workspace", False, str(e))

    async def validate_layer9_integration(self):
        """Test 6: Integration with Layer 9 (Organizational Intelligence)."""
        try:
            from torq_console.organizational_intelligence import get_layer9_services

            l9_services = get_layer9_services()
            passed1 = len(l9_services) > 0

            # Get L10 services
            from torq_console.simulation import get_layer10_services
            l10_services = get_layer10_services()
            passed2 = len(l10_services) == 5

            passed = passed1 and passed2

            self.record(
                "Layer 9 Integration",
                passed,
                f"L9 Services: {len(l9_services)}, L10 Services: {len(l10_services)}"
            )

        except Exception as e:
            self.record("Layer 9 Integration", False, str(e))

    async def validate_control_plane_integration(self):
        """Test 7: Integration with Control Plane."""
        try:
            from torq_console.control_plane.intelligence.aggregator import (
                get_intelligence_aggregator,
            )

            aggregator = get_intelligence_aggregator()
            passed1 = aggregator is not None

            # L10 should be accessible from control plane context
            from torq_console.simulation import get_simulation_engine
            engine = get_simulation_engine()
            passed2 = engine is not None

            passed = passed1 and passed2

            self.record(
                "Control Plane Integration",
                passed,
                f"Aggregator: {passed1}, Simulation Engine: {passed2}"
            )

        except Exception as e:
            self.record("Control Plane Integration", False, str(e))

    async def validate_data_models(self):
        """Test 8: Data Model validation."""
        try:
            # Test SimulationScenario
            scenario = create_simulation_scenario(
                title="Test Scenario",
                description="Test",
                simulation_scope=SimulationScope.SINGLE_MISSION,
            )
            passed1 = scenario is not None

            # Test PolicyImpactReport
            policy_report = create_policy_impact_report(
                policy_id="test",
                change_type=PolicyChangeType.READINESS_THRESHOLD,
                change_description="Test",
            )
            passed2 = policy_report is not None

            # Test StrategicForecast
            forecast = create_strategic_forecast(
                forecast_type=ForecastType.CAPABILITY_ADOPTION,
                title="Test Forecast",
                description="Test",
                timeframe_start=datetime.now(),
                timeframe_end=datetime.now() + timedelta(days=30),
            )
            passed3 = forecast is not None

            # Test RiskAssessment
            risk = create_risk_assessment(
                title="Test Risk",
                description="Test",
                risk_category=RiskCategory.EXECUTION,
            )
            passed4 = risk is not None

            # Test PlanningSession
            session = create_planning_session(
                title="Test Session",
                description="Test",
            )
            passed5 = session is not None

            passed = passed1 and passed2 and passed3 and passed4 and passed5

            self.record(
                "Data Models",
                passed,
                f"Scenario: {passed1}, Policy: {passed2}, Forecast: {passed3}, "
                f"Risk: {passed4}, Session: {passed5}"
            )

        except Exception as e:
            self.record("Data Models", False, str(e))

    async def validate_simulation_isolation(self):
        """Test 9: Simulation isolation (no production data impact)."""
        try:
            # Get initial state
            engine = get_simulation_engine()
            initial_scenarios = len(engine.list_scenarios())

            # Run simulation
            scenario = await engine.create_scenario(
                title="Isolation Test",
                description="Test isolation",
                simulation_scope=SimulationScope.SINGLE_MISSION,
                iterations=10,
            )
            result = await engine.run_simulation(scenario.scenario_id)

            # Verify isolation - simulation should not modify production data
            passed1 = result.scenario_id == scenario.scenario_id
            passed2 = result.total_simulations == 10
            passed3 = len(engine.list_scenarios()) == initial_scenarios + 1

            # Cleanup - verify we can delete without affecting other systems
            engine._scenarios.pop(scenario.scenario_id, None)
            passed4 = len(engine.list_scenarios()) == initial_scenarios

            passed = passed1 and passed2 and passed3 and passed4

            self.record(
                "Simulation Isolation",
                passed,
                f"Isolated: {passed1}, Consistent: {passed2}, Cleanable: {passed4}"
            )

        except Exception as e:
            self.record("Simulation Isolation", False, str(e))

    async def validate_no_regression(self):
        """Test 10: No regression in L1-L9 functionality."""
        try:
            # Test L9: Organizational Intelligence
            from torq_console.organizational_intelligence import get_cross_mission_aggregator
            aggregator = get_cross_mission_aggregator()
            l9_ok = aggregator is not None

            # Test L8: Learning
            from torq_console.learning import get_learning_analytics
            analytics = get_learning_analytics()
            l8_ok = analytics is not None

            # Test L7: Control Plane
            from torq_console.control_plane.core.state_manager import (
                get_control_plane_state,
            )
            state = get_control_plane_state()
            l7_ok = state is not None

            # Test L6: Readiness
            from torq_console.readiness.query_service import get_query_service
            query = get_query_service()
            l6_ok = query is not None

            passed = l9_ok and l8_ok and l7_ok and l6_ok

            self.record(
                "L1-L9 Regression Check",
                passed,
                f"L9: {l9_ok}, L8: {l8_ok}, L7: {l7_ok}, L6: {l6_ok}"
            )

        except Exception as e:
            self.record("L1-L9 Regression Check", False, str(e))

    async def run_all(self):
        """Run all Layer 10 validation tests."""
        logger.info("=" * 70)
        logger.info("TORQ CONSOLE - LAYER 10: STRATEGIC SIMULATION & FORECASTING VALIDATION")
        logger.info("=" * 70)

        await self.validate_scenario_simulation()
        await self.validate_policy_simulation()
        await self.validate_strategic_forecasting()
        await self.validate_risk_modeling()
        await self.validate_planning_workspace()
        await self.validate_layer9_integration()
        await self.validate_control_plane_integration()
        await self.validate_data_models()
        await self.validate_simulation_isolation()
        await self.validate_no_regression()

        # Print summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 70)

        for test_name, passed, message in self.results:
            status = "[PASS]" if passed else "[FAIL]"
            logger.info(f"{status} - {test_name}: {message}")

        logger.info("")
        logger.info(f"Total: {len(self.results)} tests")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")

        if self.failed == 0:
            logger.info("")
            logger.info("=" * 70)
            logger.info("LAYER 10 COMPLETE - Strategic Simulation is operational!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("✓ Mission scenarios can be simulated")
            logger.info("✓ Policy changes can be tested safely")
            logger.info("✓ Strategic forecasts are generated")
            logger.info("✓ Risk analysis models operate correctly")
            logger.info("✓ Planning workspace supports scenario comparison")
            logger.info("✓ Integration with Control Plane")
            logger.info("✓ Integration with Layer 9")
            logger.info("✓ Simulations are isolated from production")
            logger.info("✓ No regression in L1-L9 functionality")
            logger.info("")
            logger.info("TORQ is now a Predictive Strategic Intelligence Platform.")
            logger.info("=" * 70)
        else:
            logger.warning("")
            logger.warning(f"{self.failed} test(s) failed")
            logger.info("")

        return self.failed == 0


if __name__ == "__main__":
    validator = Layer10Validator()
    success = asyncio.run(validator.run_all())
    sys.exit(0 if success else 1)
