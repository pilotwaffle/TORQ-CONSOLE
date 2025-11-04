"""
Phase 1 Comprehensive Tests for ControlFlow Integration

Tests all Phase 1 components:
- Agent creation
- Integration system
- Task result models
- Research workflows
- Analysis workflows

Run with: python test_phase1_controlflow.py
"""

import os
import sys
import time
import logging
from typing import Dict, Any

# Add TORQ Console to path
sys.path.insert(0, '/home/user/TORQ-CONSOLE')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase1TestSuite:
    """Comprehensive test suite for Phase 1 ControlFlow integration."""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results: Dict[str, Any] = {}

    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        self.tests_run += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Running Test {self.tests_run}: {test_name}")
        logger.info(f"{'='*60}")

        start_time = time.time()
        try:
            result = test_func()
            execution_time = time.time() - start_time

            self.tests_passed += 1
            self.test_results[test_name] = {
                'status': 'PASSED',
                'execution_time': execution_time,
                'result': result
            }
            logger.info(f"✅ Test PASSED in {execution_time:.2f}s")
            return True

        except Exception as e:
            execution_time = time.time() - start_time
            self.tests_failed += 1
            self.test_results[test_name] = {
                'status': 'FAILED',
                'execution_time': execution_time,
                'error': str(e)
            }
            logger.error(f"❌ Test FAILED in {execution_time:.2f}s: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_01_imports(self):
        """Test 1: Verify all imports work correctly."""
        logger.info("Testing imports...")

        # Core imports
        import controlflow as cf
        import prefect

        logger.info(f"✓ ControlFlow version: {cf.__version__}")
        logger.info(f"✓ Prefect version: {prefect.__version__}")

        # TORQ ControlFlow orchestration imports
        from torq_console.orchestration import TorqControlFlowIntegration
        from torq_console.orchestration.agents import (
            create_web_search_agent,
            create_analyst_agent,
            create_writer_agent,
            create_code_agent,
            create_general_agent
        )
        from torq_console.orchestration.tasks import (
            SearchResult,
            AnalysisResult,
            ReportResult,
            CodeAnalysisResult
        )
        from torq_console.orchestration.flows import (
            research_workflow,
            analysis_workflow,
            code_analysis_workflow
        )

        logger.info("✓ All imports successful")
        return {
            'controlflow_version': cf.__version__,
            'prefect_version': prefect.__version__,
            'imports': 'all_successful'
        }

    def test_02_agent_creation(self):
        """Test 2: Create all specialized agents."""
        logger.info("Testing agent creation...")

        from torq_console.orchestration.agents import (
            create_web_search_agent,
            create_analyst_agent,
            create_writer_agent,
            create_code_agent,
            create_general_agent,
            get_default_model
        )

        # Get default model
        model = get_default_model()
        logger.info(f"✓ Default model: {model}")

        # Create agents (without actual API calls)
        agents_created = {}

        # Web search agent
        web_agent = create_web_search_agent(model)
        agents_created['web_search'] = {
            'name': web_agent.name,
            'description': web_agent.description,
            'model': web_agent.model
        }
        logger.info(f"✓ Created: {web_agent.name}")

        # Analyst agent
        analyst_agent = create_analyst_agent(model)
        agents_created['analyst'] = {
            'name': analyst_agent.name,
            'description': analyst_agent.description,
            'model': analyst_agent.model
        }
        logger.info(f"✓ Created: {analyst_agent.name}")

        # Writer agent
        writer_agent = create_writer_agent(model)
        agents_created['writer'] = {
            'name': writer_agent.name,
            'description': writer_agent.description,
            'model': writer_agent.model
        }
        logger.info(f"✓ Created: {writer_agent.name}")

        # Code agent
        code_agent = create_code_agent(model)
        agents_created['code'] = {
            'name': code_agent.name,
            'description': code_agent.description,
            'model': code_agent.model
        }
        logger.info(f"✓ Created: {code_agent.name}")

        # General agent
        general_agent = create_general_agent(model)
        agents_created['general'] = {
            'name': general_agent.name,
            'description': general_agent.description,
            'model': general_agent.model
        }
        logger.info(f"✓ Created: {general_agent.name}")

        logger.info(f"✓ All {len(agents_created)} agents created successfully")
        return agents_created

    def test_03_integration_system(self):
        """Test 3: Test TorqControlFlowIntegration."""
        logger.info("Testing integration system...")

        from torq_console.orchestration import TorqControlFlowIntegration
        from torq_console.orchestration.agents import create_general_agent

        # Create integration instance
        integration = TorqControlFlowIntegration({
            'default_model': 'anthropic/claude-sonnet-4-20250514'
        })
        logger.info("✓ Integration instance created")

        # Register an agent
        agent = create_general_agent()
        integration.register_agent('test_agent', agent, ['general', 'test'])
        logger.info("✓ Agent registered")

        # Get agent
        retrieved_agent = integration.get_agent('test_agent')
        assert retrieved_agent is not None, "Agent retrieval failed"
        logger.info("✓ Agent retrieved")

        # Get agents by capability
        general_agents = integration.get_agents_by_capability('general')
        assert len(general_agents) > 0, "Capability search failed"
        logger.info(f"✓ Found {len(general_agents)} agents with 'general' capability")

        # Get status
        status = integration.get_status()
        logger.info(f"✓ Integration status: {status}")

        # Update metrics
        integration.update_metrics(success=True, execution_time=1.5, tasks_count=3)
        metrics = integration.get_metrics()
        logger.info(f"✓ Metrics updated: {metrics}")

        return {
            'agents_registered': status['agents_registered'],
            'flows_registered': status['flows_registered'],
            'metrics': metrics
        }

    def test_04_task_models(self):
        """Test 4: Test task result models."""
        logger.info("Testing task result models...")

        from torq_console.orchestration.tasks import (
            SearchResult,
            AnalysisResult,
            ReportResult,
            CodeAnalysisResult,
            TaskStatus
        )

        # Test SearchResult
        search_result = SearchResult(
            query="test query",
            results=[
                {"title": "Test", "url": "https://test.com", "snippet": "Test snippet"}
            ],
            sources_count=1,
            search_time=1.2,
            method="test",
            success=True
        )
        logger.info(f"✓ SearchResult created: {search_result.query}")

        # Test AnalysisResult
        analysis_result = AnalysisResult(
            key_themes=["theme1", "theme2"],
            insights=["insight1", "insight2"],
            confidence=0.85,
            source_quality="high",
            summary="Test analysis"
        )
        logger.info(f"✓ AnalysisResult created: confidence={analysis_result.confidence}")

        # Test ReportResult
        report_result = ReportResult(
            title="Test Report",
            content="# Test Content",
            summary="Test summary",
            sections=["Introduction", "Conclusion"],
            sources=["https://test.com"],
            confidence=0.88,
            word_count=100
        )
        logger.info(f"✓ ReportResult created: {report_result.title}")

        # Test CodeAnalysisResult
        code_result = CodeAnalysisResult(
            language="python",
            quality_score=0.75,
            issues=[{"type": "warning", "message": "test"}],
            suggestions=["Add tests"],
            complexity="medium",
            has_tests=False,
            has_docs=True
        )
        logger.info(f"✓ CodeAnalysisResult created: {code_result.language}")

        # Test TaskStatus enum
        statuses = [status.value for status in TaskStatus]
        logger.info(f"✓ TaskStatus enum: {statuses}")

        return {
            'search_result': search_result.dict(),
            'analysis_result': analysis_result.dict(),
            'report_result': report_result.dict(),
            'code_result': code_result.dict(),
            'task_statuses': statuses
        }

    def test_05_flow_definitions(self):
        """Test 5: Test flow definitions (structure only, no execution)."""
        logger.info("Testing flow definitions...")

        from torq_console.orchestration.flows import (
            research_workflow,
            analysis_workflow,
            code_analysis_workflow
        )

        # Check that flows are callable
        assert callable(research_workflow), "research_workflow not callable"
        logger.info("✓ research_workflow is callable")

        assert callable(analysis_workflow), "analysis_workflow not callable"
        logger.info("✓ analysis_workflow is callable")

        assert callable(code_analysis_workflow), "code_analysis_workflow not callable"
        logger.info("✓ code_analysis_workflow is callable")

        # Check flow attributes (ControlFlow decorates functions)
        logger.info(f"✓ research_workflow: {research_workflow.__name__}")
        logger.info(f"✓ analysis_workflow: {analysis_workflow.__name__}")
        logger.info(f"✓ code_analysis_workflow: {code_analysis_workflow.__name__}")

        return {
            'research_workflow': 'defined',
            'analysis_workflow': 'defined',
            'code_analysis_workflow': 'defined'
        }

    def test_06_integration_registration(self):
        """Test 6: Test complete integration with agent and flow registration."""
        logger.info("Testing complete integration registration...")

        from torq_console.orchestration import TorqControlFlowIntegration
        from torq_console.orchestration.agents import (
            create_web_search_agent,
            create_analyst_agent,
            create_writer_agent,
            create_code_agent
        )
        from torq_console.orchestration.flows import (
            research_workflow,
            analysis_workflow
        )

        # Create integration
        integration = TorqControlFlowIntegration()

        # Register all agents
        model = 'anthropic/claude-sonnet-4-20250514'

        integration.register_agent(
            'web_search',
            create_web_search_agent(model),
            ['web_search', 'information_retrieval']
        )
        logger.info("✓ Registered web_search agent")

        integration.register_agent(
            'analyst',
            create_analyst_agent(model),
            ['analysis', 'insights']
        )
        logger.info("✓ Registered analyst agent")

        integration.register_agent(
            'writer',
            create_writer_agent(model),
            ['writing', 'synthesis']
        )
        logger.info("✓ Registered writer agent")

        integration.register_agent(
            'code',
            create_code_agent(model),
            ['code', 'programming']
        )
        logger.info("✓ Registered code agent")

        # Register flows
        integration.register_flow('research', research_workflow)
        logger.info("✓ Registered research flow")

        integration.register_flow('analysis', analysis_workflow)
        logger.info("✓ Registered analysis flow")

        # Get status
        status = integration.get_status()
        logger.info(f"✓ Integration status: {status}")

        # Test agent retrieval by capability
        search_agents = integration.get_agents_by_capability('web_search')
        logger.info(f"✓ Found {len(search_agents)} web_search agents")

        analysis_agents = integration.get_agents_by_capability('analysis')
        logger.info(f"✓ Found {len(analysis_agents)} analysis agents")

        return {
            'agents_registered': status['agents_registered'],
            'flows_registered': status['flows_registered'],
            'agent_list': status['agent_list'],
            'flow_list': status['flow_list']
        }

    def test_07_module_structure(self):
        """Test 7: Verify complete module structure."""
        logger.info("Testing module structure...")

        import os
        from pathlib import Path

        base_path = Path('/home/user/TORQ-CONSOLE/torq_console/orchestration')

        # Check directory structure
        expected_dirs = ['agents', 'flows', 'tasks', 'tests']
        for dir_name in expected_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} not found"
            logger.info(f"✓ Directory exists: {dir_name}")

        # Check key files
        expected_files = [
            '__init__.py',
            'integration.py',
            'agents/__init__.py',
            'agents/base_agents.py',
            'flows/__init__.py',
            'flows/research_flow.py',
            'flows/analysis_flow.py',
            'tasks/__init__.py',
            'tasks/base_tasks.py'
        ]

        files_found = []
        for file_name in expected_files:
            file_path = base_path / file_name
            assert file_path.exists(), f"File {file_name} not found"
            logger.info(f"✓ File exists: {file_name}")
            files_found.append(file_name)

        return {
            'directories': expected_dirs,
            'files': files_found,
            'structure': 'complete'
        }

    def run_all_tests(self):
        """Run all Phase 1 tests."""
        logger.info("\n" + "="*60)
        logger.info("PHASE 1 CONTROLFLOW INTEGRATION TEST SUITE")
        logger.info("="*60)

        # Run tests in order
        self.run_test("Test 1: Imports", self.test_01_imports)
        self.run_test("Test 2: Agent Creation", self.test_02_agent_creation)
        self.run_test("Test 3: Integration System", self.test_03_integration_system)
        self.run_test("Test 4: Task Models", self.test_04_task_models)
        self.run_test("Test 5: Flow Definitions", self.test_05_flow_definitions)
        self.run_test("Test 6: Integration Registration", self.test_06_integration_registration)
        self.run_test("Test 7: Module Structure", self.test_07_module_structure)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "="*60)
        logger.info("PHASE 1 TEST SUMMARY")
        logger.info("="*60)

        logger.info(f"Tests Run: {self.tests_run}")
        logger.info(f"Tests Passed: {self.tests_passed}")
        logger.info(f"Tests Failed: {self.tests_failed}")

        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        logger.info(f"Success Rate: {success_rate:.1f}%")

        logger.info("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status_symbol = "✅" if result['status'] == 'PASSED' else "❌"
            logger.info(f"{status_symbol} {test_name}: {result['status']} ({result['execution_time']:.2f}s)")

        if self.tests_failed > 0:
            logger.info("\n" + "="*60)
            logger.info("FAILED TESTS:")
            logger.info("="*60)
            for test_name, result in self.test_results.items():
                if result['status'] == 'FAILED':
                    logger.error(f"\n{test_name}:")
                    logger.error(f"  Error: {result.get('error', 'Unknown error')}")

        logger.info("\n" + "="*60)
        if self.tests_failed == 0:
            logger.info("🎉 ALL PHASE 1 TESTS PASSED!")
            logger.info("✅ Ready to proceed to Phase 2: Spec-Kit Enhancement")
        else:
            logger.info("❌ SOME TESTS FAILED")
            logger.info("⚠️  Fix issues before proceeding to Phase 2")
        logger.info("="*60)

        return self.tests_failed == 0


def main():
    """Run Phase 1 tests."""
    suite = Phase1TestSuite()
    success = suite.run_all_tests()

    # Return exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
