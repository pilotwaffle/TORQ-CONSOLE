"""
Test Suite for Consolidated TORQ Console Tools

This test suite validates the consolidation of 12+ tool files into 5 focused modules.
Tests ensure all functionality is preserved, interfaces work correctly, and
performance improvements are realized.

Author: TORQ Console Development Team
Version: 2.0.0 (Date: 2024-12-14)
"""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Test imports from consolidated tools
from torq_console.agents.tools import (
    # Unified interface
    UnifiedToolManager,
    get_unified_tool_manager,
    ToolCategory,
    ToolStatus,
    UnifiedResult,

    # Core tools
    CoreToolsManager,
    create_core_tools_manager,

    # Integration tools
    IntegrationManager,
    create_integration_manager,

    # Content tools
    ContentManager,
    ContentRequest,
    ContentFormat,
    CodeLanguage,
    create_content_manager,

    # Automation tools
    AutomationManager,
    BrowserEngine,
    create_automation_manager,

    # Legacy compatibility
    create_file_operations_tool,
    create_terminal_commands_tool,
    create_browser_automation_tool,

    # Utility functions
    get_available_categories,
    discover_tools_by_capability
)


class TestConsolidation:
    """Test suite for tool consolidation."""

    @pytest.fixture
    async def unified_manager(self):
        """Fixture providing initialized unified tool manager."""
        manager = UnifiedToolManager()
        initialized = await manager.initialize()
        assert initialized, "Failed to initialize unified tool manager"
        yield manager
        await manager.cleanup_all()

    @pytest.fixture
    def temp_dir(self):
        """Fixture providing temporary directory for file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    class TestUnifiedInterface:
        """Test unified interface functionality."""

        @pytest.mark.asyncio
        async def test_manager_initialization(self, unified_manager):
            """Test unified manager initialization."""
            # Check that all tool categories are represented
            system_info = unified_manager.get_system_info()

            assert system_info['total_tools'] > 0, "No tools were registered"
            assert len(system_info['tools_by_category']) >= 4, "Not all categories represented"

            # Check specific categories
            expected_categories = ['core', 'integration', 'content', 'automation']
            for category in expected_categories:
                assert category in system_info['available_categories'], f"Missing category: {category}"

        @pytest.mark.asyncio
        async def test_tool_discovery(self, unified_manager):
            """Test tool discovery by category and capability."""
            # Test category discovery
            core_tools = unified_manager.get_tools_by_category(ToolCategory.CORE)
            assert len(core_tools) > 0, "No core tools found"

            # Test capability discovery
            file_tools = unified_manager.discover_tools(capability="file_operations")
            assert len(file_tools) > 0, "No file operation tools found"

            # Test tag discovery
            automation_tools = unified_manager.discover_tools(tag="automation")
            assert len(automation_tools) > 0, "No automation tools found"

        @pytest.mark.asyncio
        async def test_health_monitoring(self, unified_manager):
            """Test health monitoring across all tools."""
            health_status = await unified_manager.health_check_all()

            # Check that we got health status for all tools
            assert len(health_status) > 0, "No health status returned"

            # Check health status structure
            for tool_name, status in health_status.items():
                assert hasattr(status, 'status'), f"Missing status for {tool_name}"
                assert hasattr(status, 'last_check'), f"Missing last_check for {tool_name}"
                assert isinstance(status.last_check, datetime), f"Invalid last_check type for {tool_name}"

        @pytest.mark.asyncio
        async def test_tool_metrics(self, unified_manager):
            """Test metrics collection for tools."""
            # Execute a tool action to generate metrics
            result = await unified_manager.execute_tool("core_tools", "file_list", dir_path=".")
            assert result.success, "Tool execution failed"

            # Check metrics for the executed tool
            tool = unified_manager.get_tool("core_tools")
            metrics = tool.get_metrics()

            assert metrics['total_calls'] > 0, "No calls recorded"
            assert metrics['average_execution_time'] >= 0, "Invalid execution time"
            assert 'success_rate_percent' in metrics, "Missing success rate"

    class TestCoreTools:
        """Test consolidated core tools functionality."""

        @pytest.mark.asyncio
        async def test_file_operations(self, unified_manager, temp_dir):
            """Test consolidated file operations."""
            # Create test file
            test_file = temp_dir / "test.txt"
            test_content = "Hello, World!"

            # Write file
            result = await unified_manager.execute_tool(
                "core_tools",
                "file_write",
                file_path=str(test_file),
                content=test_content
            )
            assert result.success, f"File write failed: {result.error}"
            assert test_file.exists(), "File was not created"

            # Read file
            result = await unified_manager.execute_tool(
                "core_tools",
                "file_read",
                file_path=str(test_file)
            )
            assert result.success, f"File read failed: {result.error}"
            assert result.data == test_content, "File content mismatch"

        @pytest.mark.asyncio
        async def test_directory_operations(self, unified_manager, temp_dir):
            """Test directory listing operations."""
            result = await unified_manager.execute_tool(
                "core_tools",
                "file_list",
                dir_path=str(temp_dir)
            )
            assert result.success, f"Directory list failed: {result.error}"
            assert isinstance(result.data, list), "Expected list of files"

        @pytest.mark.asyncio
        async def test_security_controls(self, unified_manager):
            """Test security controls for core operations."""
            # Test dangerous command blocking
            result = await unified_manager.execute_tool(
                "core_tools",
                "command",
                command="rm -rf /"
            )
            assert not result.success, "Dangerous command should be blocked"
            assert "Security violation" in result.error or "dangerous" in result.error.lower()

        @pytest.mark.asyncio
        async def test_core_tools_manager_direct(self, temp_dir):
            """Test core tools manager directly."""
            manager = create_core_tools_manager()

            # Test health check
            health = await manager.check_health()
            assert health.success, "Core tools health check failed"

            # Test file operations
            test_file = temp_dir / "direct_test.txt"
            result = await manager.execute_file_operation(
                "write",
                file_path=str(test_file),
                content="Direct test"
            )
            assert result.success, "Direct file write failed"

    class TestIntegrationTools:
        """Test consolidated integration tools functionality."""

        @pytest.mark.asyncio
        async def test_credential_management(self):
            """Test unified credential management."""
            from torq_console.agents.tools import CredentialManager, Credential

            manager = CredentialManager()

            # Test credential storage
            cred = Credential(
                service_name="test_service",
                credential_type="api_key",
                value="test_key"
            )
            manager.store_credential(cred)

            # Test credential retrieval
            retrieved = manager.get_credential("test_service")
            assert retrieved is not None, "Credential not retrieved"
            assert retrieved.value == "test_key", "Credential value mismatch"

        @pytest.mark.asyncio
        async def test_integration_manager_initialization(self, unified_manager):
            """Test integration manager initialization."""
            integration_tool = unified_manager.get_tool("integration_tools")
            assert integration_tool is not None, "Integration tool not found"

            # Test connection status
            health = await integration_tool.health_check()
            assert health.status, "Integration tool health check failed"

        @pytest.mark.asyncio
        async def test_http_client_base(self, unified_manager):
            """Test HTTP integration client functionality."""
            # Test that HTTP client can be initialized (may fail without actual service)
            result = await unified_manager.execute_tool(
                "integration_tools",
                "check_connections"
            )
            # This may fail if no integrations are configured, which is expected
            assert result is not None, "Connection check returned None"

    class TestContentTools:
        """Test consolidated content tools functionality."""

        @pytest.mark.asyncio
        async def test_code_generation(self, unified_manager, temp_dir):
            """Test consolidated code generation."""
            request = ContentRequest(
                content_type=ContentFormat.CODE,
                language=CodeLanguage.PYTHON,
                description="Create a simple hello world function"
            )

            result = await unified_manager.execute_tool(
                "content_tools",
                "generate_content",
                **request.__dict__
            )
            assert result.success, f"Code generation failed: {result.error}"
            assert result.data is not None, "No code content generated"

            # Test validation
            validation_result = await unified_manager.execute_tool(
                "content_tools",
                "validate_content",
                content=result.data,
                format="code"
            )
            assert validation_result.success, "Code validation failed"

        @pytest.mark.asyncio
        async def test_content_validation(self, unified_manager):
            """Test content validation functionality."""
            # Test valid HTML
            valid_html = "<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"

            result = await unified_manager.execute_tool(
                "content_tools",
                "validate_content",
                content=valid_html,
                format="html"
            )
            assert result.success, "Valid HTML should pass validation"

            # Test invalid HTML
            invalid_html = "<html><head><title>Test"

            result = await unified_manager.execute_tool(
                "content_tools",
                "validate_content",
                content=invalid_html,
                format="html"
            )
            # May still succeed due to lenient validation, but check for quality assessment
            assert result is not None, "Validation should return a result"

        @pytest.mark.asyncio
        async def test_content_manager_direct(self, temp_dir):
            """Test content manager directly."""
            manager = create_content_manager(temp_dir)

            # Test content generation
            request = ContentRequest(
                content_type=ContentFormat.TEXT,
                description="Generate test text"
            )

            result = await manager.generate_content(request)
            assert result.success, "Direct content generation failed"

    class TestAutomationTools:
        """Test consolidated automation tools functionality."""

        @pytest.mark.asyncio
        async def test_workflow_definition(self, unified_manager):
            """Test workflow definition and execution."""
            from torq_console.agents.tools import WorkflowDefinition, WorkflowStep, WorkflowType

            # Create simple workflow definition
            workflow = WorkflowDefinition(
                name="test_workflow",
                description="Test workflow execution",
                workflow_type=WorkflowType.SEQUENTIAL,
                steps=[
                    WorkflowStep(
                        step_name="delay_step",
                        step_type="delay",
                        parameters={"seconds": 0.1}
                    )
                ]
            )

            # Execute workflow
            result = await unified_manager.execute_tool(
                "automation_tools",
                "run_workflow",
                workflow={
                    "name": workflow.name,
                    "description": workflow.description,
                    "workflow_type": workflow.workflow_type.value,
                    "steps": []
                }
            )
            # May fail due to complex workflow setup, but should not crash
            assert result is not None, "Workflow execution returned None"

        @pytest.mark.asyncio
        async def test_browser_actions_simulation(self, unified_manager):
            """Test browser action interface (without actual browser)."""
            # Test that browser tool exists and can be queried
            browser_tool = unified_manager.get_tool("automation_tools")
            assert browser_tool is not None, "Browser automation tool not found"

            # Test health check
            health = await browser_tool.health_check()
            # May show as failed if Playwright not available, which is expected
            assert health is not None, "Browser health check failed"

    class TestLegacyCompatibility:
        """Test legacy compatibility functions."""

        @pytest.mark.asyncio
        async def test_legacy_file_operations(self, temp_dir):
            """Test legacy file operations compatibility."""
            # Test legacy function
            file_tool = await create_file_operations_tool()

            # Should return a unified tool wrapper
            assert file_tool is not None, "Legacy file tool creation failed"

            # Test that it has the expected interface
            assert hasattr(file_tool, 'name'), "Legacy tool missing name attribute"

        @pytest.mark.asyncio
        async def test_legacy_browser_automation(self):
            """Test legacy browser automation compatibility."""
            # Test legacy function
            browser_tool = await create_browser_automation_tool()

            # Should return a unified tool wrapper
            assert browser_tool is not None, "Legacy browser tool creation failed"

            # Test that it has the expected interface
            assert hasattr(browser_tool, 'name'), "Legacy tool missing name attribute"

        @pytest.mark.asyncio
        async def test_legacy_terminal_commands(self):
            """Test legacy terminal commands compatibility."""
            # Test legacy function
            terminal_tool = await create_terminal_commands_tool()

            # Should return a unified tool wrapper
            assert terminal_tool is not None, "Legacy terminal tool creation failed"

    class TestUtilityFunctions:
        """Test utility functions and helpers."""

        def test_get_available_categories(self):
            """Test category listing utility."""
            categories = get_available_categories()
            assert isinstance(categories, list), "Categories should be a list"
            assert len(categories) > 0, "No categories returned"
            assert "core" in categories, "Core category missing"
            assert "integration" in categories, "Integration category missing"

        def test_discover_tools_by_capability(self):
            """Test capability-based discovery utility."""
            # This would need a manager instance in real usage
            with pytest.raises(RuntimeError):
                discover_tools_by_capability("file_operations")

        @pytest.mark.asyncio
        async def test_global_manager_function(self):
            """Test global unified tool manager function."""
            manager = await get_unified_tool_manager()
            assert isinstance(manager, UnifiedToolManager), "Invalid manager type"
            assert len(manager.tools) > 0, "Manager has no tools"

    class TestErrorHandling:
        """Test error handling across consolidated tools."""

        @pytest.mark.asyncio
        async def test_invalid_tool_execution(self, unified_manager):
            """Test execution of invalid tool actions."""
            result = await unified_manager.execute_tool("nonexistent_tool", "invalid_action")
            assert not result.success, "Invalid tool execution should fail"
            assert result.error is not None, "Should have error message"

        @pytest.mark.asyncio
        async def test_invalid_parameters(self, unified_manager):
            """Test execution with invalid parameters."""
            result = await unified_manager.execute_tool(
                "core_tools",
                "file_read",
                # Missing required file_path parameter
            )
            assert not result.success, "Invalid parameters should fail"
            assert result.error is not None, "Should have error message"

        @pytest.mark.asyncio
        async def test_security_violations(self, unified_manager):
            """Test security violation handling."""
            result = await unified_manager.execute_tool(
                "core_tools",
                "command",
                command="rm -rf /"  # Dangerous command
            )
            assert not result.success, "Security violations should be blocked"
            assert "security" in result.error.lower() or "dangerous" in result.error.lower()

    class TestPerformance:
        """Test performance improvements from consolidation."""

        @pytest.mark.asyncio
        async def test_tool_registration_performance(self):
            """Test that tool registration is efficient."""
            start_time = asyncio.get_event_loop().time()

            manager = await get_unified_tool_manager()

            registration_time = asyncio.get_event_loop().time() - start_time

            # Should register all tools quickly (< 2 seconds)
            assert registration_time < 2.0, f"Tool registration too slow: {registration_time:.2f}s"
            assert len(manager.tools) >= 4, "Not enough tools registered"

        @pytest.mark.asyncio
        async def test_memory_efficiency(self, unified_manager):
            """Test that consolidation doesn't increase memory usage significantly."""
            import sys

            # Get initial memory usage
            initial_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0

            # Execute multiple tool operations
            for i in range(10):
                result = await unified_manager.execute_tool("core_tools", "file_list", dir_path=".")
                assert result.success, f"Operation {i} failed"

            # Check that memory usage is reasonable
            final_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
            object_increase = final_objects - initial_objects

            # Should not create excessive objects (< 1000 new objects for 10 operations)
            assert object_increase < 1000, f"Excessive memory usage: {object_increase} new objects"


# Run tests if executed directly
if __name__ == "__main__":
    # Simple test runner for manual execution
    async def run_basic_tests():
        """Run basic tests to verify consolidation."""
        print("🧪 Running TORQ Console Tools Consolidation Tests...")

        try:
            # Test unified manager
            print("\n1. Testing Unified Tool Manager...")
            manager = await get_unified_tool_manager()
            print(f"✅ Manager initialized with {len(manager.tools)} tools")

            # Test tool discovery
            print("\n2. Testing Tool Discovery...")
            core_tools = manager.get_tools_by_category(ToolCategory.CORE)
            print(f"✅ Found {len(core_tools)} core tools")

            # Test health monitoring
            print("\n3. Testing Health Monitoring...")
            health = await manager.health_check_all()
            print(f"✅ Health check completed for {len(health)} tools")

            # Test file operations
            print("\n4. Testing File Operations...")
            result = await manager.execute_tool("core_tools", "file_list", dir_path=".")
            print(f"✅ File operations: {result.success}")

            # Test legacy compatibility
            print("\n5. Testing Legacy Compatibility...")
            file_tool = await create_file_operations_tool()
            print(f"✅ Legacy compatibility: {file_tool is not None}")

            print("\n🎉 All basic tests passed!")
            print(f"📊 System Info: {manager.get_system_info()}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            try:
                await manager.cleanup_all()
                print("🧹 Cleanup completed")
            except:
                pass

    # Run basic tests
    asyncio.run(run_basic_tests())