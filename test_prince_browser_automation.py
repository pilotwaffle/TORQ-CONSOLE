"""
Comprehensive test suite for Browser Automation Tool integration with Prince Flowers
Tests all browser operations, error handling, and Prince integration
"""

import asyncio
import logging
import sys
from pathlib import Path
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
TEST_URL = 'https://example.com'
TEST_PASSED = 0
TEST_FAILED = 0
TEST_RESULTS = []


def test_result(test_name: str, passed: bool, message: str = ""):
    """Record test result."""
    global TEST_PASSED, TEST_FAILED

    if passed:
        TEST_PASSED += 1
        status = "✓ PASS"
        logger.info(f"{status}: {test_name}")
    else:
        TEST_FAILED += 1
        status = "✗ FAIL"
        logger.error(f"{status}: {test_name} - {message}")

    TEST_RESULTS.append({
        'test': test_name,
        'passed': passed,
        'message': message
    })


async def test_1_import_tool():
    """Test 1: Import BrowserAutomationTool and factory function."""
    try:
        from torq_console.agents.tools import BrowserAutomationTool, create_browser_automation_tool
        test_result("Import BrowserAutomationTool", True)
        return True
    except ImportError as e:
        test_result("Import BrowserAutomationTool", False, str(e))
        return False


async def test_2_tool_initialization():
    """Test 2: Initialize tool with default and custom configuration."""
    try:
        from torq_console.agents.tools import create_browser_automation_tool

        # Test default initialization
        tool = create_browser_automation_tool()
        assert tool is not None, "Tool instance is None"
        assert hasattr(tool, 'name'), "Tool missing 'name' attribute"
        assert hasattr(tool, 'execute'), "Tool missing 'execute' method"
        assert hasattr(tool, 'is_available'), "Tool missing 'is_available' method"

        # Test custom configuration
        tool_custom = create_browser_automation_tool(
            headless=False,
            browser_type='firefox',
            timeout=60000
        )
        assert tool_custom is not None, "Custom tool instance is None"
        assert tool_custom.browser_type == 'firefox', "Browser type not set correctly"
        assert tool_custom.timeout == 60000, "Timeout not set correctly"

        test_result("Tool initialization", True)
        return True
    except Exception as e:
        test_result("Tool initialization", False, str(e))
        return False


async def test_3_tool_availability():
    """Test 3: Check tool availability status."""
    try:
        from torq_console.agents.tools import create_browser_automation_tool

        tool = create_browser_automation_tool()
        is_available = tool.is_available()

        # Tool should report availability status
        assert isinstance(is_available, bool), "is_available() should return bool"

        if not is_available:
            logger.warning("Playwright not installed - some tests will be skipped")

        test_result("Tool availability check", True)
        return is_available
    except Exception as e:
        test_result("Tool availability check", False, str(e))
        return False


async def test_4_navigate_operation():
    """Test 4: Test navigate operation."""
    try:
        from torq_console.agents.tools import create_browser_automation_tool

        tool = create_browser_automation_tool()

        if not tool.is_available():
            test_result("Navigate operation", True, "SKIPPED - Playwright not installed")
            return True

        # Execute navigate
        result = await tool.execute(action='navigate', url=TEST_URL)

        assert result is not None, "Result is None"
        assert 'success' in result, "Result missing 'success' key"
        assert 'result' in result or 'error' in result, "Result missing 'result' or 'error' key"
        assert 'execution_time' in result, "Result missing 'execution_time' key"
        assert 'timestamp' in result, "Result missing 'timestamp' key"

        if result['success']:
            assert result['result']['url'] == TEST_URL, "URL mismatch"
            assert 'final_url' in result['result'], "Missing final_url"
            assert 'title' in result['result'], "Missing title"

        test_result("Navigate operation", result['success'], result.get('error', ''))
        return result['success']
    except Exception as e:
        test_result("Navigate operation", False, str(e))
        return False


async def test_5_screenshot_operation():
    """Test 5: Test screenshot operation."""
    try:
        from torq_console.agents.tools import create_browser_automation_tool

        tool = create_browser_automation_tool()

        if not tool.is_available():
            test_result("Screenshot operation", True, "SKIPPED - Playwright not installed")
            return True

        # Create temp directory for screenshot
        with tempfile.TemporaryDirectory() as temp_dir:
            screenshot_path = str(Path(temp_dir) / 'test_screenshot.png')

            # Navigate first
            await tool.execute(action='navigate', url=TEST_URL)

            # Take screenshot
            result = await tool.execute(action='screenshot', path=screenshot_path)

            assert result is not None, "Result is None"
            assert 'success' in result, "Result missing 'success' key"

            if result['success']:
                assert Path(screenshot_path).exists(), "Screenshot file not created"
                assert result['result']['path'] == str(Path(screenshot_path).resolve()), "Path mismatch"
                assert result['result']['size_bytes'] > 0, "Screenshot file is empty"

        test_result("Screenshot operation", result['success'], result.get('error', ''))
        return result['success']
    except Exception as e:
        test_result("Screenshot operation", False, str(e))
        return False


async def test_6_error_handling():
    """Test 6: Test error handling for invalid operations."""
    try:
        from torq_console.agents.tools import create_browser_automation_tool

        tool = create_browser_automation_tool()

        if not tool.is_available():
            test_result("Error handling", True, "SKIPPED - Playwright not installed")
            return True

        # Test missing required parameter (navigate without URL)
        result = await tool.execute(action='navigate')
        assert not result['success'], "Should fail without URL"
        assert 'error' in result, "Should have error message"
        assert 'url is required' in result['error'].lower(), "Should mention missing URL"

        # Test invalid action
        result = await tool.execute(action='invalid_action')
        assert not result['success'], "Should fail with invalid action"
        assert 'error' in result, "Should have error message"
        assert 'unknown action' in result['error'].lower(), "Should mention unknown action"

        # Test timeout on non-existent selector
        await tool.execute(action='navigate', url=TEST_URL)
        result = await tool.execute(
            action='wait_for',
            selector='#nonexistent-element-12345',
            timeout_ms=1000  # Short timeout
        )
        assert not result['success'], "Should timeout on non-existent element"
        assert 'error' in result, "Should have error message"

        test_result("Error handling", True)
        return True
    except Exception as e:
        test_result("Error handling", False, str(e))
        return False


async def test_7_tool_metadata():
    """Test 7: Test tool metadata and information."""
    try:
        from torq_console.agents.tools import create_browser_automation_tool

        tool = create_browser_automation_tool()

        # Check basic attributes
        assert hasattr(tool, 'name'), "Missing 'name' attribute"
        assert hasattr(tool, 'description'), "Missing 'description' attribute"
        assert hasattr(tool, 'cost'), "Missing 'cost' attribute"
        assert hasattr(tool, 'success_rate'), "Missing 'success_rate' attribute"
        assert hasattr(tool, 'avg_time'), "Missing 'avg_time' attribute"

        # Check get_tool_info method
        tool_info = tool.get_tool_info()
        assert 'name' in tool_info, "Tool info missing 'name'"
        assert 'description' in tool_info, "Tool info missing 'description'"
        assert 'parameters' in tool_info, "Tool info missing 'parameters'"
        assert 'available' in tool_info, "Tool info missing 'available'"

        # Validate parameters
        params = tool_info['parameters']
        assert 'action' in params, "Missing 'action' parameter"
        assert params['action']['required'] is True, "'action' should be required"
        assert 'enum' in params['action'], "'action' should have enum"

        expected_actions = ['navigate', 'click', 'fill', 'screenshot', 'get_text', 'wait_for', 'evaluate']
        for action in expected_actions:
            assert action in params['action']['enum'], f"Missing action: {action}"

        # Check format_for_prince method
        test_result_data = {
            'success': True,
            'result': {'url': TEST_URL, 'final_url': TEST_URL, 'status': 200, 'title': 'Test'},
            'execution_time': 1.5,
            'timestamp': '2025-01-01T00:00:00'
        }
        formatted = tool.format_for_prince(test_result_data)
        assert isinstance(formatted, str), "format_for_prince should return string"
        assert len(formatted) > 0, "Formatted output should not be empty"

        test_result("Tool metadata", True)
        return True
    except Exception as e:
        test_result("Tool metadata", False, str(e))
        return False


async def test_8_prince_integration():
    """Test 8: Test Prince Flowers integration."""
    try:
        from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

        # Check if browser_automation is in available_tools
        prince = TORQPrinceFlowers()

        assert 'browser_automation' in prince.available_tools, "browser_automation not in available_tools"

        tool_info = prince.available_tools['browser_automation']
        assert 'name' in tool_info, "Tool info missing 'name'"
        assert 'description' in tool_info, "Tool info missing 'description'"
        assert 'cost' in tool_info, "Tool info missing 'cost'"

        # Check if _execute_browser_automation method exists
        assert hasattr(prince, '_execute_browser_automation'), "Prince missing _execute_browser_automation method"

        test_result("Prince integration", True)
        return True
    except AssertionError as e:
        test_result("Prince integration", False, f"Integration incomplete: {str(e)}")
        return False
    except Exception as e:
        test_result("Prince integration", False, str(e))
        return False


async def run_all_tests():
    """Run all tests and report results."""
    logger.info("=" * 80)
    logger.info("Browser Automation Tool - Comprehensive Test Suite")
    logger.info("=" * 80)

    # Run tests in sequence
    await test_1_import_tool()
    await test_2_tool_initialization()
    await test_3_tool_availability()
    await test_4_navigate_operation()
    await test_5_screenshot_operation()
    await test_6_error_handling()
    await test_7_tool_metadata()
    await test_8_prince_integration()

    # Report results
    logger.info("=" * 80)
    logger.info("TEST RESULTS")
    logger.info("=" * 80)

    for result in TEST_RESULTS:
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        message = f" - {result['message']}" if result['message'] else ""
        logger.info(f"{status}: {result['test']}{message}")

    logger.info("=" * 80)
    logger.info(f"Total: {TEST_PASSED + TEST_FAILED} tests")
    logger.info(f"Passed: {TEST_PASSED} ({100 * TEST_PASSED / (TEST_PASSED + TEST_FAILED):.1f}%)")
    logger.info(f"Failed: {TEST_FAILED}")
    logger.info("=" * 80)

    if TEST_FAILED == 0:
        logger.info("✓ ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"✗ {TEST_FAILED} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    # Run tests
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
