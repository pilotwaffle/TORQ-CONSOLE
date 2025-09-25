#!/usr/bin/env python3
"""
TORQ CONSOLE Integration Test.

Tests the complete integration between TORQ CONSOLE and Claude Code capabilities.
"""

import asyncio
import sys
import tempfile
from pathlib import Path
import logging

# Add TORQ CONSOLE to path
sys.path.insert(0, str(Path(__file__).parent))

from torq_console.core.console import TorqConsole
from torq_console.core.config import TorqConfig
from torq_console.mcp.client import MCPClient
from torq_console.mcp.claude_code_bridge import ClaudeCodeBridge
from torq_console.utils.visual_diff import VisualDiffEngine
from torq_console.ui.web import WebUI


class TorqIntegrationTest:
    """Integration test suite for TORQ CONSOLE + Claude Code."""

    def __init__(self):
        self.logger = self._setup_logging()
        self.test_repo = None
        self.console = None
        self.results = []

    def _setup_logging(self):
        """Setup logging for tests."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    async def run_all_tests(self):
        """Run all integration tests."""
        self.logger.info("🚀 Starting TORQ CONSOLE Integration Tests")

        try:
            # Setup test environment
            await self.setup_test_environment()

            # Run tests
            await self.test_configuration()
            await self.test_console_initialization()
            await self.test_mcp_client()
            await self.test_claude_code_bridge()
            await self.test_visual_diff_engine()
            await self.test_web_ui_setup()
            await self.test_end_to_end_workflow()

            # Report results
            self.report_results()

        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            return False
        finally:
            await self.cleanup()

        return all(result['passed'] for result in self.results)

    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger.info("Setting up test environment...")

        # Create temporary test repository
        self.test_repo = Path(tempfile.mkdtemp(prefix="torq_test_"))
        self.logger.info(f"Test repository: {self.test_repo}")

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=self.test_repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@torq.dev"], cwd=self.test_repo, check=True)
        subprocess.run(["git", "config", "user.name", "TORQ Test"], cwd=self.test_repo, check=True)

        # Create test files
        (self.test_repo / "test.py").write_text("""
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")

        (self.test_repo / "README.md").write_text("""
# Test Repository

This is a test repository for TORQ CONSOLE integration testing.
""")

    async def test_configuration(self):
        """Test configuration system."""
        self.logger.info("Testing configuration system...")

        try:
            # Test default config creation
            config = TorqConfig.create_default()
            assert config.version == "0.60.0"
            assert len(config.mcp_servers) > 0
            assert len(config.ai_models) > 0

            # Test config validation
            errors = config.validate()
            # Some errors expected due to missing API keys in test env

            # Test config save/load
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                config_path = Path(f.name)

            config.save(config_path)
            assert config_path.exists()

            loaded_config = TorqConfig.load(config_path)
            assert loaded_config.version == config.version

            config_path.unlink()

            self.results.append({
                'test': 'configuration',
                'passed': True,
                'message': 'Configuration system working correctly'
            })

        except Exception as e:
            self.results.append({
                'test': 'configuration',
                'passed': False,
                'message': f'Configuration test failed: {e}'
            })

    async def test_console_initialization(self):
        """Test console initialization."""
        self.logger.info("Testing console initialization...")

        try:
            config = TorqConfig.create_default()

            # Initialize console
            self.console = TorqConsole(
                config=config,
                repo_path=self.test_repo,
                model="claude-3-5-sonnet-20241022"
            )

            assert self.console.repo_path == self.test_repo
            assert self.console.model == "claude-3-5-sonnet-20241022"
            assert self.console.git_manager is not None
            assert self.console.mcp_client is not None
            assert self.console.claude_code_bridge is not None

            self.results.append({
                'test': 'console_initialization',
                'passed': True,
                'message': 'Console initialized successfully'
            })

        except Exception as e:
            self.results.append({
                'test': 'console_initialization',
                'passed': False,
                'message': f'Console initialization failed: {e}'
            })

    async def test_mcp_client(self):
        """Test MCP client functionality."""
        self.logger.info("Testing MCP client...")

        try:
            client = MCPClient()

            # Test that client initializes without connection
            assert len(client.get_connected_endpoints()) == 0
            assert not client.is_connected("test://endpoint")

            # Test health check on non-existent connection
            health = await client.health_check()
            assert health is False

            # Test listing tools with no connections
            tools = await client.list_tools()
            assert tools == []

            self.results.append({
                'test': 'mcp_client',
                'passed': True,
                'message': 'MCP client basic functionality working'
            })

        except Exception as e:
            self.results.append({
                'test': 'mcp_client',
                'passed': False,
                'message': f'MCP client test failed: {e}'
            })

    async def test_claude_code_bridge(self):
        """Test Claude Code bridge."""
        self.logger.info("Testing Claude Code bridge...")

        try:
            client = MCPClient()
            bridge = ClaudeCodeBridge(client)

            # Test bridge initialization
            assert bridge.mcp_client is not None
            assert len(bridge.tool_mappings) > 0
            assert len(bridge.context_strategies) > 0

            # Test strategy determination
            strategy = bridge._determine_edit_strategy(
                "fix the bug in auth.py",
                ["auth.py"],
                {}
            )
            assert strategy == "debugging"

            strategy = bridge._determine_edit_strategy(
                "add a new user registration feature",
                [],
                {}
            )
            assert strategy == "feature"

            # Test context classification
            context_type = bridge._classify_context_need("help me debug this error")
            assert context_type == "debugging"

            context_type = bridge._classify_context_need("give me ideas for this feature")
            assert context_type == "ideation"

            self.results.append({
                'test': 'claude_code_bridge',
                'passed': True,
                'message': 'Claude Code bridge functioning correctly'
            })

        except Exception as e:
            self.results.append({
                'test': 'claude_code_bridge',
                'passed': False,
                'message': f'Claude Code bridge test failed: {e}'
            })

    async def test_visual_diff_engine(self):
        """Test visual diff engine."""
        self.logger.info("Testing visual diff engine...")

        try:
            diff_engine = VisualDiffEngine()

            # Test tool availability check
            tools = diff_engine.get_available_tools()
            assert isinstance(tools, dict)
            assert 'git' in tools  # Git should always be available

            # Test language detection
            test_file = self.test_repo / "test.py"
            language = diff_engine._detect_language(test_file)
            assert language == "python"

            # Test file preview
            preview = await diff_engine.get_file_preview(test_file, tool="rich")
            assert isinstance(preview, str)
            assert len(preview) > 0

            # Test content diff
            before = "def old_function():\n    pass"
            after = "def new_function():\n    return True"

            diff = await diff_engine.get_diff(
                content_before=before,
                content_after=after,
                tool="rich"
            )
            assert isinstance(diff, str)
            assert len(diff) > 0

            self.results.append({
                'test': 'visual_diff_engine',
                'passed': True,
                'message': 'Visual diff engine working correctly'
            })

        except Exception as e:
            self.results.append({
                'test': 'visual_diff_engine',
                'passed': False,
                'message': f'Visual diff engine test failed: {e}'
            })

    async def test_web_ui_setup(self):
        """Test web UI setup."""
        self.logger.info("Testing web UI setup...")

        try:
            if self.console is None:
                config = TorqConfig.create_default()
                self.console = TorqConsole(config=config, repo_path=self.test_repo)

            # Initialize web UI
            web_ui = WebUI(self.console)
            assert web_ui.console is not None
            assert web_ui.app is not None
            assert web_ui.diff_engine is not None

            # Test that FastAPI app is configured
            assert len(web_ui.app.routes) > 0

            self.results.append({
                'test': 'web_ui_setup',
                'passed': True,
                'message': 'Web UI setup successful'
            })

        except Exception as e:
            self.results.append({
                'test': 'web_ui_setup',
                'passed': False,
                'message': f'Web UI setup failed: {e}'
            })

    async def test_end_to_end_workflow(self):
        """Test end-to-end workflow."""
        self.logger.info("Testing end-to-end workflow...")

        try:
            if self.console is None:
                config = TorqConfig.create_default()
                self.console = TorqConsole(config=config, repo_path=self.test_repo)

            # Start a session
            session = await self.console.start_session()
            assert session is not None
            assert 'id' in session
            assert self.console.current_session is not None

            # Test file detection
            test_message = "update the hello world function"
            files = await self.console.detect_relevant_files(test_message)
            assert isinstance(files, list)
            # Should detect test.py as relevant

            # Test diff generation
            diff_content = await self.console.get_visual_diff()
            assert isinstance(diff_content, str)

            # Test session info
            session_info = self.console.get_session_info()
            assert isinstance(session_info, dict)
            assert 'active_files' in session_info or session_info.get('active_files') is not None

            self.results.append({
                'test': 'end_to_end_workflow',
                'passed': True,
                'message': 'End-to-end workflow functional'
            })

        except Exception as e:
            self.results.append({
                'test': 'end_to_end_workflow',
                'passed': False,
                'message': f'End-to-end workflow failed: {e}'
            })

    def report_results(self):
        """Report test results."""
        self.logger.info("\n" + "="*60)
        self.logger.info("🧪 TORQ CONSOLE Integration Test Results")
        self.logger.info("="*60)

        passed = 0
        failed = 0

        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            self.logger.info(f"{status} - {result['test']}: {result['message']}")

            if result['passed']:
                passed += 1
            else:
                failed += 1

        self.logger.info("="*60)
        self.logger.info(f"Total: {len(self.results)} tests, {passed} passed, {failed} failed")

        if failed == 0:
            self.logger.info("🎉 All tests passed! TORQ CONSOLE is ready for Claude Code integration.")
        else:
            self.logger.warning(f"⚠️  {failed} test(s) failed. Review before production use.")

        self.logger.info("="*60)

    async def cleanup(self):
        """Cleanup test environment."""
        try:
            if self.console:
                await self.console.shutdown()

            if self.test_repo and self.test_repo.exists():
                import shutil
                shutil.rmtree(self.test_repo)
                self.logger.info("Test environment cleaned up")

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


async def main():
    """Run integration tests."""
    test_suite = TorqIntegrationTest()
    success = await test_suite.run_all_tests()

    if success:
        print("\n🚀 TORQ CONSOLE is ready! Run 'python -m torq_console.cli --help' to get started.")
        return 0
    else:
        print("\n❌ Integration tests failed. Please review the logs above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)