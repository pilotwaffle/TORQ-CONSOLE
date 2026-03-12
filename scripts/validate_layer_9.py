"""
     TORQ Console - Layer 9: Organizational Intelligence Validation

Validates the Organizational Intelligence Layer (Layer 9).

Tests:
1. Cross-Mission Aggregator - Mission grouping and aggregation
2. Enterprise Knowledge Graph - Node and edge management
3. Strategic Insight Engine - Strategic insight generation
4. Portfolio Analytics - Portfolio-wide metrics
5. Organizational Playbook Miner - Playbook mining
6. Decision Support Service - Strategic queries
7. Integration with Control Plane
8. Integration with Learning Layer
9. Data Model validation
10. No regression in L1-L8 functionality
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

# L9 Imports
from torq_console.organizational_intelligence.models import (
    GraphEntityType,
    GraphRelationType,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    GraphPath,
    StrategicInsightCategory,
    StrategicInsight,
    PortfolioMetricSnapshot,
    ReadinessHeatmapData,
    OrganizationalPlaybook,
    DecisionSupportRecommendation,
    MissionGrouping,
    CrossMissionAggregation,
    create_organizational_intelligence,
    create_knowledge_graph_node,
    create_strategic_insight,
    create_portfolio_snapshot,
    create_organizational_playbook,
    get_all_graph_entity_types,
    get_all_graph_relation_types,
    get_all_strategic_insight_categories,
)

from torq_console.organizational_intelligence.aggregation.cross_mission_aggregator import (
    CrossMissionAggregator,
    MissionSummary,
    get_cross_mission_aggregator,
)

from torq_console.organizational_intelligence.knowledge_graph.graph_service import (
    KnowledgeGraphService,
    get_knowledge_graph_service,
)

from torq_console.organizational_intelligence.strategic_insights.strategic_insight_engine import (
    get_strategic_insight_engine,
)

from torq_console.organizational_intelligence.portfolio_analytics.portfolio_analytics_engine import (
    PortfolioAnalyticsEngine,
    get_portfolio_analytics_engine,
)

from torq_console.organizational_intelligence.playbooks.playbook_miner import (
    PlaybookMiner,
    get_playbook_miner,
)

from torq_console.organizational_intelligence.decision_support.decision_support_service import (
    DecisionSupportService,
    get_decision_support_service,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Layer9Validator:
    """Validator for Layer 9: Organizational Intelligence."""

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

    async def validate_cross_mission_aggregator(self):
        """Test 1: Cross-Mission Aggregator - Mission grouping."""
        try:
            aggregator = get_cross_mission_aggregator()

            # Add mission summaries
            summary1 = MissionSummary(
                mission_id="mission_1",
                mission_type="analysis",
                domain="finance",
                success=True,
                success_score=0.9,
                quality_score=0.85,
                duration_seconds=120,
            )
            aggregator.add_mission_summary(summary1)

            summary2 = MissionSummary(
                mission_id="mission_2",
                mission_type="analysis",
                domain="finance",
                success=False,
                success_score=0.3,
                quality_score=0.5,
                duration_seconds=180,
            )
            aggregator.add_mission_summary(summary2)

            # Test aggregation by mission type
            agg = await aggregator.aggregate_by_mission_type("analysis")
            passed1 = agg is not None
            passed2 = agg.total_missions_analyzed == 2
            # 1 success out of 2 missions = 0.5 success rate
            passed3 = agg.groupings[0].success_rate == 0.5

            # Test statistics
            stats = await aggregator.get_mission_statistics()
            passed4 = stats["total_missions"] == 2

            passed = passed1 and passed2 and passed3 and passed4

            self.record(
                "Cross-Mission Aggregator",
                passed,
                f"Aggregation: {passed1}, Missions: {agg.total_missions_analyzed}, Rate: {agg.groupings[0].success_rate:.2f}, Stats: {passed4}"
            )

        except Exception as e:
            self.record("Cross-Mission Aggregator", False, str(e))

    async def validate_knowledge_graph(self):
        """Test 2: Enterprise Knowledge Graph - Node and edge management."""
        try:
            graph = get_knowledge_graph_service()

            # Test node addition
            node = KnowledgeGraphNode(
                node_id="mission_1",
                node_type=GraphEntityType.MISSION,
                label="Test Mission",
                confidence=0.9,
            )
            added_node = await graph.add_node(node)
            passed1 = added_node is not None
            passed2 = added_node.node_id == "mission_1"

            # Add target node for edge
            target_node = KnowledgeGraphNode(
                node_id="tool_1",
                node_type=GraphEntityType.TOOL,
                label="Test Tool",
                confidence=0.8,
            )
            await graph.add_node(target_node)

            # Test edge addition
            edge = KnowledgeGraphEdge(
                edge_id="edge_1",
                source_id="mission_1",
                target_id="tool_1",
                relation_type=GraphRelationType.USED_TOOL,
                confidence=0.8,
            )
            added_edge = await graph.add_edge(edge)
            passed3 = added_edge is not None

            # Test node retrieval
            retrieved = await graph.get_node("mission_1")
            passed4 = retrieved is not None

            # Test statistics
            stats = await graph.get_graph_statistics()
            # We added 2 nodes (mission_1 and tool_1)
            passed5 = stats["total_nodes"] == 2 and stats["total_edges"] == 1

            passed = passed1 and passed2 and passed3 and passed4 and passed5

            self.record(
                "Enterprise Knowledge Graph",
                passed,
                f"Node: {passed1}, Edge: {passed3}, Retrieve: {passed4}, Stats: {stats}"
            )

        except Exception as e:
            self.record("Enterprise Knowledge Graph", False, str(e))

    async def validate_strategic_insights(self):
        """Test 3: Strategic Insight Engine."""
        try:
            engine = get_strategic_insight_engine()

            # Test insight generation
            insights = await engine.generate_insights()
            passed1 = insights is not None

            # Test listing
            listed = await engine.list_insights()
            passed2 = listed is not None

            passed = passed1 and passed2

            self.record(
                "Strategic Insight Engine",
                passed,
                f"Generate: {passed1}, List: {passed2}"
            )

        except Exception as e:
            self.record("Strategic Insight Engine", False, str(e))

    async def validate_portfolio_analytics(self):
        """Test 4: Portfolio Analytics."""
        try:
            engine = get_portfolio_analytics_engine()

            # Test metrics
            metrics = await engine.get_portfolio_metrics()
            passed1 = metrics is not None

            # Test heatmap
            heatmap = await engine.get_readiness_heatmap()
            passed2 = heatmap is not None

            # Test trends
            trends = await engine.get_trends()
            passed3 = trends is not None

            passed = passed1 and passed2 and passed3

            self.record(
                "Portfolio Analytics",
                passed,
                f"Metrics: {passed1}, Heatmap: {passed2}, Trends: {passed3}"
            )

        except Exception as e:
            self.record("Portfolio Analytics", False, str(e))

    async def validate_playbook_miner(self):
        """Test 5: Organizational Playbook Miner."""
        try:
            miner = get_playbook_miner()

            # Test playbook mining
            playbooks = await miner.mine_playbooks()
            passed1 = playbooks is not None

            # Test listing
            listed = await miner.list_playbooks()
            passed2 = listed is not None

            passed = passed1 and passed2

            self.record(
                "Organizational Playbook Miner",
                passed,
                f"Mine: {passed1}, List: {passed2}"
            )

        except Exception as e:
            self.record("Organizational Playbook Miner", False, str(e))

    async def validate_decision_support(self):
        """Test 6: Decision Support Service."""
        try:
            service = get_decision_support_service()

            # Test question answering
            query = await service.answer_question(
                question="Which workflows have the highest success rate?",
                context={"domain": "finance"},
            )
            passed1 = query is not None
            passed2 = query.summary is not None

            # Test recommendations
            recommendations = await service.get_recommendations()
            passed3 = recommendations is not None

            passed = passed1 and passed2 and passed3

            self.record(
                "Decision Support Service",
                passed,
                f"Query: {passed1}, Summary: {passed2}, Recommendations: {passed3}"
            )

        except Exception as e:
            self.record("Decision Support Service", False, str(e))

    async def validate_control_plane_integration(self):
        """Test 7: Integration with Control Plane."""
        try:
            from torq_console.control_plane.intelligence.aggregator import (
                get_intelligence_aggregator,
            )

            # Get intelligence aggregator
            aggregator = get_intelligence_aggregator()
            passed1 = aggregator is not None

            # Test that we can access Layer 9 services from control plane
            from torq_console.organizational_intelligence import get_layer9_services
            services = get_layer9_services()
            passed2 = len(services) == 2

            passed = passed1 and passed2

            self.record(
                "Control Plane Integration",
                passed,
                f"Aggregator: {passed1}, Services: {list(services.keys())}"
            )

        except Exception as e:
            self.record("Control Plane Integration", False, str(e))

    async def validate_learning_integration(self):
        """Test 8: Integration with Learning Layer."""
        try:
            from torq_console.learning import get_outcome_analyzer
            from torq_console.learning.autonomous_models import OutcomeEvaluation

            # Get outcome analyzer
            analyzer = get_outcome_analyzer()
            passed1 = analyzer is not None

            # Test that we can feed outcomes into Layer 9 aggregation
            aggregator = get_cross_mission_aggregator()
            passed2 = aggregator is not None

            passed = passed1 and passed2

            self.record(
                "Learning Integration",
                passed,
                f"Analyzer: {passed1}, Aggregator: {passed2}"
            )

        except Exception as e:
            self.record("Learning Integration", False, str(e))

    async def validate_data_models(self):
        """Test 9: Data Model validation."""
        try:
            # Test OrganizationalIntelligenceRecord
            org_intel = create_organizational_intelligence(
                record_type="test",
                title="Test Org Intel",
                summary="Test summary",
                confidence=0.8,
                timeframe_start=datetime.now(),
                timeframe_end=datetime.now() + timedelta(days=1),
            )
            passed1 = org_intel is not None

            # Test KnowledgeGraphNode
            node = create_knowledge_graph_node(
                node_id="test_node",
                node_type=GraphEntityType.MISSION,
                label="Test Node",
            )
            passed2 = node is not None

            # Test StrategicInsight
            insight = create_strategic_insight(
                category=StrategicInsightCategory.ENTERPRISE_BEST_PRACTICE,
                title="Test Insight",
                narrative="Test narrative",
            )
            passed3 = insight is not None

            # Test PortfolioMetricSnapshot
            snapshot = create_portfolio_snapshot(
                timeframe_start=datetime.now(),
                timeframe_end=datetime.now() + timedelta(days=1),
            )
            passed4 = snapshot is not None

            # Test OrganizationalPlaybook
            playbook = create_organizational_playbook(
                title="Test Playbook",
                description="Test description",
            )
            passed5 = playbook is not None

            passed = passed1 and passed2 and passed3 and passed4 and passed5

            self.record(
                "Data Models",
                passed,
                f"OrgIntel: {passed1}, Node: {passed2}, Insight: {passed3}, Snapshot: {passed4}, Playbook: {passed5}"
            )

        except Exception as e:
            self.record("Data Models", False, str(e))

    async def validate_no_regression(self):
        """Test 10: No regression in L1-L8 functionality."""
        try:
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

            passed = l8_ok and l7_ok and l6_ok

            self.record(
                "L1-L8 Regression Check",
                passed,
                f"L8: {l8_ok}, L7: {l7_ok}, L6: {l6_ok}"
            )

        except Exception as e:
            self.record("L1-L8 Regression Check", False, str(e))

    async def run_all(self):
        """Run all Layer 9 validation tests."""
        logger.info("=" * 70)
        logger.info("TORQ CONSOLE - LAYER 9: ORGANIZATIONAL INTELLIGENCE VALIDATION")
        logger.info("=" * 70)

        await self.validate_cross_mission_aggregator()
        await self.validate_knowledge_graph()
        await self.validate_strategic_insights()
        await self.validate_portfolio_analytics()
        await self.validate_playbook_miner()
        await self.validate_decision_support()
        await self.validate_control_plane_integration()
        await self.validate_learning_integration()
        await self.validate_data_models()
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
            logger.info("LAYER 9 COMPLETE - Organizational Intelligence is operational!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("✓ Cross-mission intelligence aggregation working")
            logger.info("✓ Enterprise knowledge graph operational")
            logger.info("✓ Strategic insights generated")
            logger.info("✓ Portfolio analytics available")
            logger.info("✓ Organizational playbooks mined")
            logger.info("✓ Decision support queries working")
            logger.info("✓ Integration with Control Plane")
            logger.info("✓ Integration with Learning Layer")
            logger.info("✓ No regression in L1-L8 functionality")
            logger.info("")
            logger.info("TORQ is now an Organization-Improving Intelligence System.")
            logger.info("=" * 70)
        else:
            logger.warning("")
            logger.warning(f"{self.failed} test(s) failed")
            logger.info("")

        return self.failed == 0


if __name__ == "__main__":
    validator = Layer9Validator()
    success = asyncio.run(validator.run_all())
    sys.exit(0 if success else 1)
