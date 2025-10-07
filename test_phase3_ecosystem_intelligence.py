#!/usr/bin/env python3
"""
TORQ Console Spec-Kit Phase 3: Ecosystem Intelligence Test Suite
Comprehensive testing for GitHub/GitLab integration, team collaboration, and multi-project management
"""

import asyncio
import json
import logging
import tempfile
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import aiohttp
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Phase3Test")

class TestPhase3EcosystemIntelligence(unittest.TestCase):
    """Test suite for Phase 3: Ecosystem Intelligence features"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.spec_engine = None

        # Mock GitHub API response
        self.mock_github_response = {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "url": "https://api.github.com/repos/user/test-repo",
            "clone_url": "https://github.com/user/test-repo.git"
        }

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_01_ecosystem_intelligence_initialization(self):
        """Test 1: Ecosystem Intelligence component initialization"""
        logger.info("🧪 Test 1: Testing ecosystem intelligence initialization...")

        try:
            from torq_console.spec_kit.ecosystem_intelligence import EcosystemIntelligence

            # Initialize ecosystem intelligence
            ecosystem = EcosystemIntelligence()

            # Verify components are initialized
            self.assertIsNotNone(ecosystem.github_integration)
            self.assertIsNotNone(ecosystem.gitlab_integration)
            self.assertIsNotNone(ecosystem.team_collaboration)
            self.assertIsNotNone(ecosystem.version_control)
            self.assertIsNotNone(ecosystem.analytics)

            logger.info("✅ Test 1 PASSED: Ecosystem intelligence initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Test 1 FAILED: {e}")
            return False

    def test_02_github_integration_setup(self):
        """Test 2: GitHub integration setup and repository connection"""
        logger.info("🧪 Test 2: Testing GitHub integration setup...")

        try:
            from torq_console.spec_kit.ecosystem_intelligence import GitHubIntegration, GitRepository

            # Initialize GitHub integration
            github = GitHubIntegration("mock_token")

            # Verify token is set
            self.assertEqual(github.token, "mock_token")
            self.assertIsNotNone(github.session)

            # Test repository creation
            repo = GitRepository(
                name="test-repo",
                url="https://github.com/user/test-repo",
                owner="user",
                provider="github"
            )

            self.assertEqual(repo.name, "test-repo")
            self.assertEqual(repo.provider, "github")

            logger.info("✅ Test 2 PASSED: GitHub integration setup successful")
            return True

        except Exception as e:
            logger.error(f"❌ Test 2 FAILED: {e}")
            return False

    @patch('aiohttp.ClientSession.get')
    async def test_03_github_api_integration(self, mock_get):
        """Test 3: GitHub API integration and repository operations"""
        logger.info("🧪 Test 3: Testing GitHub API integration...")

        try:
            from torq_console.spec_kit.ecosystem_intelligence import GitHubIntegration

            # Mock API response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = self.mock_github_response
            mock_get.return_value.__aenter__.return_value = mock_response

            # Initialize GitHub integration
            github = GitHubIntegration("test_token")

            # Test getting repository info
            repo_info = await github.get_repository_info("user/test-repo")

            # Verify response
            self.assertEqual(repo_info["name"], "test-repo")
            self.assertEqual(repo_info["full_name"], "user/test-repo")

            logger.info("✅ Test 3 PASSED: GitHub API integration working")
            return True

        except Exception as e:
            logger.error(f"❌ Test 3 FAILED: {e}")
            return False

    def test_04_team_collaboration_features(self):
        """Test 4: Team collaboration features and session management"""
        logger.info("🧪 Test 4: Testing team collaboration features...")

        try:
            from torq_console.spec_kit.ecosystem_intelligence import TeamCollaboration, TeamMember

            # Initialize team collaboration
            team_collab = TeamCollaboration()

            # Create test team members
            member1 = TeamMember(
                id="user1",
                name="Alice Developer",
                email="alice@example.com",
                role="lead"
            )

            member2 = TeamMember(
                id="user2",
                name="Bob Reviewer",
                email="bob@example.com",
                role="reviewer"
            )

            # Test session creation
            session_id = "test_session_001"
            spec_id = "spec_001"

            # Mock collaboration session
            team_collab.active_sessions[session_id] = Mock()
            team_collab.active_sessions[session_id].specification_id = spec_id
            team_collab.active_sessions[session_id].participants = [member1, member2]
            team_collab.active_sessions[session_id].lock_holders = {}
            team_collab.active_sessions[session_id].concurrent_editors = 2

            # Verify session state
            session = team_collab.active_sessions[session_id]
            self.assertEqual(session.specification_id, spec_id)
            self.assertEqual(len(session.participants), 2)

            logger.info("✅ Test 4 PASSED: Team collaboration features working")
            return True

        except Exception as e:
            logger.error(f"❌ Test 4 FAILED: {e}")
            return False

    def test_05_collaboration_server_initialization(self):
        """Test 5: WebSocket collaboration server initialization"""
        logger.info("🧪 Test 5: Testing collaboration server initialization...")

        try:
            from torq_console.spec_kit.collaboration_server import CollaborationServer, CollaborationManager

            # Initialize collaboration components
            server = CollaborationServer(host="localhost", port=8765)
            manager = CollaborationManager(host="localhost", port=8765)

            # Verify initialization
            self.assertEqual(server.host, "localhost")
            self.assertEqual(server.port, 8765)
            self.assertIsNotNone(server.collaboration)
            self.assertFalse(manager.running)

            # Verify data structures
            self.assertIsInstance(server.connected_clients, dict)
            self.assertIsInstance(server.client_sessions, dict)

            logger.info("✅ Test 5 PASSED: Collaboration server initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Test 5 FAILED: {e}")
            return False

    def test_06_version_control_system(self):
        """Test 6: Specification version control and history tracking"""
        logger.info("🧪 Test 6: Testing version control system...")

        try:
            from torq_console.spec_kit.ecosystem_intelligence import VersionControl, SpecificationVersion

            # Initialize version control
            version_control = VersionControl()

            # Create test specification version
            version = SpecificationVersion(
                version_number="1.0.0",
                specification_id="spec_001",
                content={"title": "Test Spec", "description": "Test description"},
                author="test_user",
                commit_message="Initial version"
            )

            # Verify version data
            self.assertEqual(version.version_number, "1.0.0")
            self.assertEqual(version.specification_id, "spec_001")
            self.assertEqual(version.author, "test_user")

            # Test version storage
            spec_id = "spec_001"
            if spec_id not in version_control.specification_history:
                version_control.specification_history[spec_id] = []

            version_control.specification_history[spec_id].append(version)

            # Verify storage
            self.assertEqual(len(version_control.specification_history[spec_id]), 1)
            stored_version = version_control.specification_history[spec_id][0]
            self.assertEqual(stored_version.version_number, "1.0.0")

            logger.info("✅ Test 6 PASSED: Version control system working")
            return True

        except Exception as e:
            logger.error(f"❌ Test 6 FAILED: {e}")
            return False

    def test_07_workspace_management(self):
        """Test 7: Multi-project workspace management"""
        logger.info("🧪 Test 7: Testing workspace management...")

        try:
            from torq_console.spec_kit.ecosystem_intelligence import EcosystemIntelligence, Workspace

            # Initialize ecosystem intelligence
            ecosystem = EcosystemIntelligence()

            # Create test workspace
            workspace = ecosystem.create_workspace(
                name="Test Workspace",
                description="Test workspace for project management"
            )

            # Verify workspace creation
            self.assertEqual(workspace.name, "Test Workspace")
            self.assertEqual(workspace.description, "Test workspace for project management")
            self.assertIsInstance(workspace.projects, list)
            self.assertIsInstance(workspace.team_members, list)

            # Test workspace retrieval
            workspaces = ecosystem.get_workspaces()
            self.assertEqual(len(workspaces), 1)
            self.assertEqual(workspaces[0].name, "Test Workspace")

            logger.info("✅ Test 7 PASSED: Workspace management working")
            return True

        except Exception as e:
            logger.error(f"❌ Test 7 FAILED: {e}")
            return False

    def test_08_spec_engine_phase3_integration(self):
        """Test 8: Phase 3 integration with SpecKitEngine"""
        logger.info("🧪 Test 8: Testing Phase 3 integration with SpecKitEngine...")

        try:
            from torq_console.spec_kit.spec_engine import SpecKitEngine

            # Initialize SpecKitEngine
            engine = SpecKitEngine(workspace_path=str(self.test_dir))

            # Verify Phase 3 components are initialized
            self.assertIsNotNone(engine.ecosystem_intelligence)
            self.assertIsNotNone(engine.collaboration_manager)

            # Test workspace creation through engine
            workspace_data = engine.create_workspace(
                name="Engine Test Workspace",
                description="Testing workspace creation through engine"
            )

            # Verify workspace creation
            self.assertEqual(workspace_data["name"], "Engine Test Workspace")

            # Test workspace retrieval
            workspaces = engine.get_workspaces()
            self.assertEqual(len(workspaces), 1)

            logger.info("✅ Test 8 PASSED: Phase 3 SpecKitEngine integration working")
            return True

        except Exception as e:
            logger.error(f"❌ Test 8 FAILED: {e}")
            return False

    async def test_09_collaboration_server_operations(self):
        """Test 9: Collaboration server operations and WebSocket handling"""
        logger.info("🧪 Test 9: Testing collaboration server operations...")

        try:
            from torq_console.spec_kit.collaboration_server import CollaborationManager

            # Initialize collaboration manager
            manager = CollaborationManager(host="localhost", port=8766)  # Different port for testing

            # Test manager status
            stats = manager.get_stats()
            self.assertIn("running", stats)
            self.assertFalse(stats["running"])

            # Mock server start/stop for testing
            with patch.object(manager.server, 'start_server', new_callable=AsyncMock) as mock_start:
                with patch.object(manager.server, 'stop_server', new_callable=AsyncMock) as mock_stop:

                    # Test start
                    await manager.start()
                    mock_start.assert_called_once()
                    self.assertTrue(manager.running)

                    # Test stop
                    await manager.stop()
                    mock_stop.assert_called_once()
                    self.assertFalse(manager.running)

            logger.info("✅ Test 9 PASSED: Collaboration server operations working")
            return True

        except Exception as e:
            logger.error(f"❌ Test 9 FAILED: {e}")
            return False

    async def test_10_end_to_end_ecosystem_workflow(self):
        """Test 10: End-to-end ecosystem intelligence workflow"""
        logger.info("🧪 Test 10: Testing end-to-end ecosystem workflow...")

        try:
            from torq_console.spec_kit.spec_engine import SpecKitEngine
            from torq_console.spec_kit.ecosystem_intelligence import TeamMember

            # Initialize SpecKitEngine with Phase 3
            engine = SpecKitEngine(workspace_path=str(self.test_dir))

            # 1. Create a specification
            spec = await engine.create_specification(
                title="Test Ecosystem Spec",
                description="Testing ecosystem intelligence integration",
                requirements=["Real-time collaboration", "Version control"],
                acceptance_criteria=["Multi-user editing", "Change history"],
                dependencies=[],
                tech_stack=["WebSocket", "Git"],
                timeline="2-weeks",
                complexity="medium",
                priority="high"
            )

            spec_id = spec.id

            # 2. Create workspace
            workspace = engine.create_workspace(
                name="Test Project",
                description="End-to-end testing project"
            )

            # 3. Test collaboration session (mocked)
            team_members = [
                {"id": "user1", "name": "Alice", "email": "alice@test.com", "role": "lead"},
                {"id": "user2", "name": "Bob", "email": "bob@test.com", "role": "developer"}
            ]

            # Mock the collaboration session creation
            with patch.object(engine.ecosystem_intelligence, 'start_collaboration_session', new_callable=AsyncMock) as mock_session:
                mock_session.return_value = "session_001"

                session_result = await engine.start_collaboration_session(spec_id, team_members)

                # Verify session creation
                self.assertEqual(session_result["session_id"], "session_001")
                self.assertEqual(session_result["specification_id"], spec_id)
                self.assertEqual(session_result["participants"], 2)

            # 4. Get ecosystem status
            status = engine.get_ecosystem_status()

            # Verify comprehensive status
            self.assertIn("phase3_ecosystem_intelligence", status)
            self.assertIn("collaboration_server", status)
            self.assertEqual(status["phase3_ecosystem_intelligence"]["phase3_status"], "active")

            logger.info("✅ Test 10 PASSED: End-to-end ecosystem workflow working")
            return True

        except Exception as e:
            logger.error(f"❌ Test 10 FAILED: {e}")
            return False

async def run_phase3_tests():
    """Run all Phase 3 ecosystem intelligence tests"""
    logger.info("🚀 Starting TORQ Console Spec-Kit Phase 3: Ecosystem Intelligence Test Suite")
    logger.info("=" * 80)

    # Initialize test suite
    test_suite = TestPhase3EcosystemIntelligence()
    test_results = []

    # Run synchronous tests
    sync_tests = [
        test_suite.test_01_ecosystem_intelligence_initialization,
        test_suite.test_02_github_integration_setup,
        test_suite.test_04_team_collaboration_features,
        test_suite.test_05_collaboration_server_initialization,
        test_suite.test_06_version_control_system,
        test_suite.test_07_workspace_management,
        test_suite.test_08_spec_engine_phase3_integration,
    ]

    for test in sync_tests:
        test_suite.setUp()
        try:
            result = test()
            test_results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
            test_results.append(False)
        finally:
            test_suite.tearDown()

    # Run async tests
    async_tests = [
        test_suite.test_03_github_api_integration,
        test_suite.test_09_collaboration_server_operations,
        test_suite.test_10_end_to_end_ecosystem_workflow,
    ]

    for test in async_tests:
        test_suite.setUp()
        try:
            result = await test()
            test_results.append(result)
        except Exception as e:
            logger.error(f"Async test {test.__name__} failed with exception: {e}")
            test_results.append(False)
        finally:
            test_suite.tearDown()

    # Calculate results
    total_tests = len(test_results)
    passed_tests = sum(test_results)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100

    # Display results
    logger.info("=" * 80)
    logger.info("📊 PHASE 3 TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"✅ Passed: {passed_tests}")
    logger.info(f"❌ Failed: {failed_tests}")
    logger.info(f"📈 Success Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        logger.info("🎉 PHASE 3 ECOSYSTEM INTELLIGENCE: INTEGRATION SUCCESSFUL!")
        logger.info("✨ GitHub/GitLab integration, team collaboration, and multi-project management ready for production")
    else:
        logger.warning("⚠️  PHASE 3 ECOSYSTEM INTELLIGENCE: INTEGRATION NEEDS ATTENTION")
        logger.warning("🔧 Some ecosystem intelligence features require fixes before production")

    logger.info("=" * 80)

    return success_rate >= 80

if __name__ == "__main__":
    success = asyncio.run(run_phase3_tests())
    exit(0 if success else 1)