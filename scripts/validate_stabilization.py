"""
     TORQ Console - Post-Layer 10 Stabilization Validation

Validates the stabilization components added after Layer 10 deployment.

Tests:
1. Simulation Calibration Engine - Forecast error tracking and parameter tuning
2. Observability Metrics - Simulation performance and risk metrics collection
3. Decision Audit System - Strategic decision artifact storage
4. Simulation Isolation Hardening - Verify simulation cannot mutate production
5. Cross-Layer Integration - Verify stabilization integrates with L1-L10
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

# L10 Stabilization Imports
from torq_console.simulation.calibration.calibration_engine import (
    SimulationCalibrationEngine,
    get_calibration_engine,
    ForecastError,
    CalibrationMetrics,
    CalibrationContext,
)

from torq_console.simulation.observability.metrics import (
    SimulationMetricsExporter,
    get_metrics_exporter,
    SimulationPerformanceTracker,
    RiskMetricsCollector,
    track_simulation_metrics,
    MetricBatch,
)

from torq_console.simulation.audit.decision_audit import (
    DecisionAuditService,
    get_decision_audit_service,
    AuditArtifactType,
    DecisionStatus,
    StrategicDecisionRecord,
)

from torq_console.simulation.models import (
    SimulationScope,
    SimulationResult,
    SimulationStatus,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StabilizationValidator:
    """Validator for Post-Layer 10 Stabilization components."""

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

    async def validate_calibration_engine(self):
        """Test 1: Simulation Calibration Engine."""
        try:
            calibration = get_calibration_engine()

            # Record a forecast error
            scenario_id = uuid4()
            forecast_id = uuid4()

            # Mock prediction
            from torq_console.simulation.models import SimulationResult
            predicted = SimulationResult(
                scenario_id=scenario_id,
                predicted_outcomes={"success_rate": 0.75, "avg_duration": 120.0, "avg_quality": 0.8},
                total_simulations=100,
                success_rate=0.75,
                avg_duration=120.0,
                avg_quality=0.8,
                confidence=0.8,
                status=SimulationStatus.COMPLETED,
            )

            # Mock actual outcome
            actual = {
                "success": True,
                "duration": 130.0,
                "quality": 0.75,
            }

            error = await calibration.record_forecast_error(
                scenario_id=scenario_id,
                forecast_id=forecast_id,
                predicted_result=predicted,
                actual_outcome=actual,
            )

            passed1 = error is not None
            passed2 = error.mean_absolute_error >= 0

            # Calculate metrics
            metrics = await calibration.calculate_calibration_metrics()
            passed3 = metrics is not None
            passed4 = metrics.mean_absolute_error is not None

            # Calibrate parameters
            params = await calibration.calibrate_simulation_parameters(metrics)
            passed5 = params is not None
            passed6 = "volatility_multiplier" in params

            # Get accuracy summary
            summary = calibration.get_forecast_accuracy_summary()
            passed7 = summary is not None
            passed8 = "total_forecasts" in summary

            passed = passed1 and passed2 and passed3 and passed4 and passed5 and passed6 and passed7 and passed8

            self.record(
                "Simulation Calibration Engine",
                passed,
                f"Error Recording: {passed1}, Metrics: {passed3}, Calibration: {passed5}, "
                f"Parameters: {list(params.keys())}, Summary: {passed7}"
            )

        except Exception as e:
            self.record("Simulation Calibration Engine", False, str(e))

    async def validate_observability_metrics(self):
        """Test 2: Observability Metrics."""
        try:
            exporter = get_metrics_exporter()

            # Get trackers
            perf_tracker = exporter.get_performance_tracker()
            passed1 = perf_tracker is not None

            risk_collector = exporter.get_risk_collector()
            passed2 = risk_collector is not None

            # Record some test metrics
            perf_tracker.record_simulation(150.0, 100)
            perf_tracker.record_outcome(0.8, 0.75)

            risk_collector.record_risk_assessment("execution", 0.3, "low")
            risk_collector.record_policy_simulation()

            # Get summaries
            perf_summary = perf_tracker.get_summary()
            passed3 = "avg_runtime_ms" in perf_summary
            passed4 = perf_summary["avg_runtime_ms"] == 150.0

            risk_summary = risk_collector.get_summary()
            passed5 = risk_summary is not None
            passed6 = "total_risk_assessments" in risk_summary

            # Export metrics batch
            batch = await exporter.export_metrics_batch()
            passed7 = batch is not None
            passed8 = len(batch.metrics) > 0

            passed = passed1 and passed2 and passed3 and passed4 and passed5 and passed6 and passed7 and passed8

            self.record(
                "Observability Metrics",
                passed,
                f"Performance Tracker: {passed1}, Risk Collector: {passed2}, "
                f"Perf Summary: {passed3}, Risk Summary: {passed5}, Export: {passed7}, "
                f"Metrics Count: {len(batch.metrics)}"
            )

        except Exception as e:
            self.record("Observability Metrics", False, str(e))

    async def validate_decision_audit(self):
        """Test 3: Decision Audit System."""
        try:
            audit = get_decision_audit_service()

            # Begin decision process
            scenario_id = uuid4()
            record = await audit.begin_decision_process(
                scenario_id=scenario_id,
                scenario_config={"mission_type": "analysis"},
                title="Test Decision",
                created_by="validator",
            )
            passed1 = record is not None
            passed2 = record.decision_id is not None

            # Record simulation results
            sim_result = {"success_rate": 0.75, "total_simulations": 100}
            await audit.record_simulation_results(
                decision_id=record.decision_id,
                simulation_result=sim_result,
                forecast_data={"trend": "improving"},
            )

            # Record operator decision
            updated = await audit.record_operator_decision(
                decision_id=record.decision_id,
                status=DecisionStatus.APPROVED,
                decision_maker="validator",
                rationale="Test rationale",
            )
            passed3 = updated is not None
            passed4 = updated.operator_decision == DecisionStatus.APPROVED

            # List decisions
            decisions = audit.list_decisions()
            passed5 = decisions is not None
            passed6 = len(decisions) >= 1  # At least our test decision

            passed = passed1 and passed2 and passed3 and passed4 and passed5 and passed6

            self.record(
                "Decision Audit System",
                passed,
                f"Begin Process: {passed1}, Record Decision: {passed3}, Status: {passed4}, "
                f"List: {passed5}, Count: {len(decisions) if decisions else 0}"
            )

        except Exception as e:
            self.record("Decision Audit System", False, str(e))

    async def validate_simulation_isolation(self):
        """Test 4: Simulation Isolation Hardening."""
        try:
            from torq_console.simulation.scenario_engine.simulation_engine import (
                get_simulation_engine,
            )
            from torq_console.organizational_intelligence import (
                get_cross_mission_aggregator,
            )

            sim_engine = get_simulation_engine()
            agg = get_cross_mission_aggregator()

            # Get initial aggregator state
            initial_count = len(agg._mission_summaries)

            # Run simulation (should not affect aggregator)
            scenario = await sim_engine.create_scenario(
                title="Isolation Test",
                description="Test isolation from production",
                simulation_scope=SimulationScope.SINGLE_MISSION,
                iterations=10,
            )
            result = await sim_engine.run_simulation(scenario.scenario_id)

            # Verify aggregator wasn't affected
            final_count = len(agg._mission_summaries)
            passed1 = final_count == initial_count
            passed2 = result.total_simulations == 10

            # Verify simulation data is isolated
            passed3 = scenario.scenario_id in sim_engine._scenarios
            passed4 = result.result_id in sim_engine._results

            # Cleanup should work without affecting production
            sim_engine._scenarios.pop(scenario.scenario_id, None)
            passed5 = len(agg._mission_summaries) == initial_count

            passed = passed1 and passed2 and passed3 and passed4 and passed5

            self.record(
                "Simulation Isolation Hardening",
                passed,
                f"Aggregator Unaffected: {passed1}, Simulation Isolated: {passed3}, "
                f"Cleanup Safe: {passed5}"
            )

        except Exception as e:
            self.record("Simulation Isolation Hardening", False, str(e))

    async def validate_cross_layer_integration(self):
        """Test 5: Cross-Layer Integration."""
        try:
            # Test L10 core services
            from torq_console.simulation import get_layer10_services
            l10_services = get_layer10_services()
            passed1 = len(l10_services) == 8  # 5 core + 3 stabilization

            # Test stabilization services
            passed2 = "calibration_engine" in l10_services
            passed3 = "metrics_exporter" in l10_services
            passed4 = "decision_audit" in l10_services

            # Test L9 integration
            from torq_console.organizational_intelligence import get_layer9_services
            l9_services = get_layer9_services()
            passed5 = len(l9_services) > 0

            # Test L8 integration
            from torq_console.learning import get_learning_analytics
            l8 = get_learning_analytics()
            passed6 = l8 is not None

            # Test Control Plane integration
            from torq_console.control_plane.intelligence.aggregator import (
                get_intelligence_aggregator,
            )
            aggregator = get_intelligence_aggregator()
            passed7 = aggregator is not None

            passed = passed1 and passed2 and passed3 and passed4 and passed5 and passed6 and passed7

            self.record(
                "Cross-Layer Integration",
                passed,
                f"L10 Services: {len(l10_services)}, Stabilization: {passed2}/{passed3}/{passed4}, "
                f"L9: {passed5}, L8: {passed6}, Control Plane: {passed7}"
            )

        except Exception as e:
            self.record("Cross-Layer Integration", False, str(e))

    async def run_all(self):
        """Run all stabilization validation tests."""
        logger.info("=" * 70)
        logger.info("TORQ CONSOLE - POST-LAYER 10 STABILIZATION VALIDATION")
        logger.info("=" * 70)

        await self.validate_calibration_engine()
        await self.validate_observability_metrics()
        await self.validate_decision_audit()
        await self.validate_simulation_isolation()
        await self.validate_cross_layer_integration()

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
            logger.info("STABILIZATION COMPLETE - Layer 10 is hardened and calibrated!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Stabilization Achievements:")
            logger.info("✓ Simulation Calibration Engine operational")
            logger.info("✓ Observability Metrics collection working")
            logger.info("✓ Decision Audit System tracking decisions")
            logger.info("✓ Simulation Isolation verified")
            logger.info("✓ Cross-Layer Integration maintained")
            logger.info("")
            logger.info("TORQ is ready for Layer 11: Distributed Intelligence Fabric")
            logger.info("=" * 70)
        else:
            logger.warning("")
            logger.warning(f"{self.failed} test(s) failed")
            logger.info("")

        return self.failed == 0


if __name__ == "__main__":
    validator = StabilizationValidator()
    success = asyncio.run(validator.run_all())
    sys.exit(0 if success else 1)
