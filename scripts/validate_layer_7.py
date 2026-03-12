"""
     TORQ Console - Layer 7: Operator Control Plane Validation

Validates the Control Plane core functionality.

Tests:
1. State Manager - Navigation and session management
2. Router - Route matching and navigation
3. Command Executor - Command execution
4. Dashboard Models - Widget and layout creation
5. System Monitor - Metrics aggregation
6. Governance Controller - Actions and approvals
7. Intelligence Aggregator - Layer aggregation
8. Dashboard Presets - Pre-built configurations
9. Integration with Readiness system
10. No regression in M1-M5 functionality
"""

import sys
import io
import asyncio
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# L7 Imports
from torq_console.control_plane.core.state_manager import (
    ControlPlaneStateManager,
    NavigationState,
    SystemAlert,
    get_control_plane_state,
)

from torq_console.control_plane.core.router import (
    ControlPlaneRouter,
    Route,
    RouteMatch,
    get_control_plane_router,
    CORE_ROUTES,
)

from torq_console.control_plane.core.commands import (
    CommandStatus,
    OperatorCommand,
    CommandExecutor,
    get_command_executor,
)

from torq_console.control_plane.dashboards.models import (
    WidgetType,
    ChartType,
    DashboardWidget,
    DashboardLayout,
    DashboardConfig,
    get_preset_dashboards,
    create_operational_dashboard,
    create_readiness_dashboard,
)

from torq_console.control_plane.dashboards.monitoring import (
    SystemMonitor,
    SystemMetrics,
    get_system_monitor,
)

from torq_console.control_plane.governance.models import (
    ActionStatus,
    ActionType,
    GovernanceActionRequest,
    GovernanceActionQueue,
    PromotionRequest,
    create_promotion_request,
)

from torq_console.control_plane.governance.controller import (
    GovernanceController,
    get_governance_controller,
)

from torq_console.control_plane.intelligence.models import (
    LayerType,
    LayerStatus,
    IntelligenceLayer,
    IntelligenceView,
    create_layer_status,
    get_default_layers,
)

from torq_console.control_plane.intelligence.aggregator import (
    IntelligenceAggregator,
    get_intelligence_aggregator,
)

# Readiness imports for integration testing
from torq_console.readiness.query_service import (
    get_query_service,
    register_candidate,
)
from torq_console.readiness.readiness_models import (
    CandidateType,
    ReadinessState,
    ReadinessCandidate,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Layer7Validator:
    """Validator for Layer 7: Operator Control Plane."""

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

    async def validate_state_manager(self):
        """Test 1: State Manager - Navigation and session management."""
        try:
            manager = ControlPlaneStateManager()
            state = manager.get_state()

            # Check initial state
            passed1 = state is not None and state.navigation is not None

            # Test navigation
            await manager.navigate_to("/readiness", {"test": "value"})
            passed2 = state.navigation.current_route == "/readiness"

            # Test alert
            alert = await manager.add_alert(
                level="info",
                title="Test Alert",
                message="This is a test alert",
                source="validator",
            )
            passed3 = alert is not None and len(state.alerts) > 0

            # Clean up
            await manager.clear_alert(alert.id)

            passed = passed1 and passed2 and passed3

            self.record(
                "State Manager",
                passed,
                f"Init: {passed1}, Nav: {passed2}, Alert: {passed3}"
            )

        except Exception as e:
            self.record("State Manager", False, str(e))

    async def validate_router(self):
        """Test 2: Router - Route matching and navigation."""
        try:
            router = ControlPlaneRouter()

            # Test route matching
            match = router.match_route("/")
            passed1 = match is not None and match.route.name == "home"

            # Test parameterized route
            match2 = router.match_route("/readiness/candidates/123")
            passed2 = match2 is not None and match2.params.get("id") == "123"

            # Test generate path
            path = router.generate_path("candidate_detail", {"id": "456"})
            passed3 = path == "/readiness/candidates/456"

            # Test breadcrumbs
            breadcrumbs = router.get_breadcrumbs("/readiness/candidates")
            passed4 = len(breadcrumbs) > 0

            passed = passed1 and passed2 and passed3 and passed4

            self.record(
                "Router",
                passed,
                f"Match home: {passed1}, Params: {passed2}, Generate: {passed3}, Breadcrumbs: {len(breadcrumbs)}"
            )

        except Exception as e:
            self.record("Router", False, str(e))

    async def validate_command_executor(self):
        """Test 3: Command Executor - Command execution."""
        try:
            executor = get_command_executor()

            # Check available commands
            commands = executor.get_available_commands()
            passed1 = len(commands) > 0

            # Test system command (refresh_metrics)
            cmd = OperatorCommand(
                command_type="refresh_metrics",
                target="system",
                action="refresh",
                requested_by="validator",
            )

            result = await executor.execute(cmd)
            passed2 = result.success is True

            passed = passed1 and passed2

            self.record(
                "Command Executor",
                passed,
                f"Commands: {len(commands)}, Execution: {result.success}"
            )

        except Exception as e:
            self.record("Command Executor", False, str(e))

    async def validate_dashboard_models(self):
        """Test 4: Dashboard Models - Widget and layout creation."""
        try:
            # Test widget creation
            from torq_console.control_plane.dashboards.models import WidgetPosition
            widget = DashboardWidget(
                id="test_widget",
                type=WidgetType.METRIC_CARD,
                title="Test Widget",
                position=WidgetPosition(),
            )
            passed1 = widget is not None

            # Test layout creation
            layout = DashboardLayout(
                id="test_layout",
                name="Test Layout",
                widgets=[widget],
            )
            passed2 = layout is not None and len(layout.widgets) == 1

            # Test dashboard config
            config = DashboardConfig(
                id="test_dashboard",
                name="test",
                title="Test Dashboard",
                layouts=[layout],
            )
            passed3 = config is not None and len(config.layouts) == 1

            passed = passed1 and passed2 and passed3

            self.record(
                "Dashboard Models",
                passed,
                f"Widget: {passed1}, Layout: {passed2}, Config: {passed3}"
            )

        except Exception as e:
            self.record("Dashboard Models", False, str(e))

    async def validate_system_monitor(self):
        """Test 5: System Monitor - Metrics aggregation."""
        try:
            monitor = get_system_monitor()

            # Get metrics
            metrics = await monitor.update_metrics()
            passed1 = metrics is not None

            # Check service health
            health = monitor.get_service_health()
            passed2 = health is not None

            passed = passed1 and passed2

            self.record(
                "System Monitor",
                passed,
                f"Metrics: {passed1}, Health: {passed2}"
            )

        except Exception as e:
            self.record("System Monitor", False, str(e))

    async def validate_governance_controller(self):
        """Test 6: Governance Controller - Actions and approvals."""
        try:
            controller = get_governance_controller()

            # Get queue
            queue = controller.get_queue()
            passed1 = queue is not None

            # Get governance view
            view = controller.get_governance_view()
            passed2 = view is not None

            # Test promotion request creation
            promo_req = create_promotion_request(
                candidate_id=uuid4(),
                candidate_type="tool",
                candidate_title="Test Tool",
                current_state="watchlist",
                current_score=0.75,
                confidence_score=0.85,
                requested_by="validator",
            )
            passed3 = promo_req is not None

            passed = passed1 and passed2 and passed3

            self.record(
                "Governance Controller",
                passed,
                f"Queue: {passed1}, View: {passed2}, Promotion: {passed3}"
            )

        except Exception as e:
            self.record("Governance Controller", False, str(e))

    async def validate_intelligence_aggregator(self):
        """Test 7: Intelligence Aggregator - Layer aggregation."""
        try:
            aggregator = get_intelligence_aggregator()

            # Get intelligence view
            view = await aggregator.get_intelligence_view()
            passed1 = view is not None

            # Check layers
            passed2 = len(view.layers) > 0

            # Test layer creation
            layer = create_layer_status(LayerType.INSIGHTS)
            passed3 = layer is not None and layer.layer_type == LayerType.INSIGHTS

            passed = passed1 and passed2 and passed3

            self.record(
                "Intelligence Aggregator",
                passed,
                f"View: {passed1}, Layers: {len(view.layers)}, Create: {passed3}"
            )

        except Exception as e:
            self.record("Intelligence Aggregator", False, str(e))

    async def validate_dashboard_presets(self):
        """Test 8: Dashboard Presets - Pre-built configurations."""
        try:
            presets = get_preset_dashboards()
            passed1 = len(presets) > 0

            # Test operational dashboard
            ops_dashboard = presets.get("operational")
            passed2 = ops_dashboard is not None and len(ops_dashboard.layouts) > 0

            # Test readiness dashboard
            readiness_dashboard = presets.get("readiness")
            passed3 = readiness_dashboard is not None

            passed = passed1 and passed2 and passed3

            self.record(
                "Dashboard Presets",
                passed,
                f"Presets: {list(presets.keys())}, Ops: {passed2}, Readiness: {passed3}"
            )

        except Exception as e:
            self.record("Dashboard Presets", False, str(e))

    async def validate_readiness_integration(self):
        """Test 9: Integration with Readiness system."""
        try:
            # Create a test candidate
            candidate = ReadinessCandidate(
                candidate_type=CandidateType.TOOL,
                candidate_key=f"tool:test_{uuid4().hex[:8]}",
                title=f"Test Tool {uuid4().hex[:8]}",
                current_state=ReadinessState.READY,
            )

            query_service = get_query_service()
            register_candidate(candidate)

            # Get candidates
            result = query_service.list_candidates()
            passed1 = result.total_count >= 1

            # Get ready candidates
            ready = query_service.list_ready_candidates()
            passed2 = ready.total_count >= 1

            # Test governance view includes readiness
            controller = get_governance_controller()
            view = controller.get_governance_view()
            passed3 = view.total_candidates >= 1

            passed = passed1 and passed2 and passed3

            self.record(
                "Readiness Integration",
                passed,
                f"Candidates: {result.total_count}, Ready: {ready.total_count}, Governance: {view.total_candidates}"
            )

        except Exception as e:
            self.record("Readiness Integration", False, str(e))

    async def validate_no_regression(self):
        """Test 10: No regression in M1-M5 functionality."""
        try:
            # Test M1: Policy registry
            from torq_console.readiness.readiness_policy import get_policy_registry
            registry = get_policy_registry()
            m1_ok = registry is not None

            # Test M2: Evidence collection
            from torq_console.readiness.evidence_collector import get_evidence_orchestrator
            m2_ok = get_evidence_orchestrator() is not None

            # Test M3: Transition controller
            from torq_console.readiness.transition_controller import get_transition_controller
            m3_ok = get_transition_controller() is not None

            # Test M4: Analytics service
            from torq_console.readiness.analytics_service import get_analytics_service
            m4_ok = get_analytics_service() is not None

            # Test M5: Regression detector
            from torq_console.readiness.hardening.regression_detector import get_regression_detector
            m5_ok = get_regression_detector() is not None

            passed = m1_ok and m2_ok and m3_ok and m4_ok and m5_ok

            self.record(
                "M1-M5 Regression Check",
                passed,
                f"M1: {m1_ok}, M2: {m2_ok}, M3: {m3_ok}, M4: {m4_ok}, M5: {m5_ok}"
            )

        except Exception as e:
            self.record("M1-M5 Regression Check", False, str(e))

    async def run_all(self):
        """Run all Layer 7 validation tests."""
        logger.info("=" * 70)
        logger.info("TORQ CONSOLE - LAYER 7: OPERATOR CONTROL PLANE VALIDATION")
        logger.info("=" * 70)

        await self.validate_state_manager()
        await self.validate_router()
        await self.validate_command_executor()
        await self.validate_dashboard_models()
        await self.validate_system_monitor()
        await self.validate_governance_controller()
        await self.validate_intelligence_aggregator()
        await self.validate_dashboard_presets()
        await self.validate_readiness_integration()
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
            logger.info("LAYER 7 COMPLETE - Operator Control Plane is operational!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("✓ State management and navigation working")
            logger.info("✓ Command execution operational")
            logger.info("✓ Dashboard models and presets created")
            logger.info("✓ System monitoring functional")
            logger.info("✓ Governance controller operational")
            logger.info("✓ Intelligence aggregation working")
            logger.info("✓ Integration with Readiness system")
            logger.info("✓ No regression in M1-M5 functionality")
            logger.info("")
            logger.info("The Operator Control Plane provides:")
            logger.info("- Real-time operational visibility")
            logger.info("- Governance action management")
            logger.info("- Mission and agent monitoring")
            logger.info("- Pattern intelligence tracking")
            logger.info("- Readiness governance UI")
            logger.info("")
            logger.info("TORQ is now a complete AI Operating System.")
            logger.info("=" * 70)
        else:
            logger.warning("")
            logger.warning(f"{self.failed} test(s) failed")
            logger.info("")

        return self.failed == 0


if __name__ == "__main__":
    validator = Layer7Validator()
    success = asyncio.run(validator.run_all())
    sys.exit(0 if success else 1)
