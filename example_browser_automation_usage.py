"""
Browser Automation Tool - Usage Examples
Demonstrates all supported browser automation operations
"""

import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def example_1_basic_navigation():
    """Example 1: Basic web page navigation."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 1: Basic Navigation")
    logger.info("=" * 80)

    tool = create_browser_automation_tool()

    if not tool.is_available():
        logger.error("Playwright not installed. Run: pip install playwright && playwright install")
        return

    # Navigate to a website
    result = await tool.execute(
        action='navigate',
        url='https://example.com'
    )

    if result['success']:
        logger.info(f"✓ Navigated successfully")
        logger.info(f"  Final URL: {result['result']['final_url']}")
        logger.info(f"  Page Title: {result['result']['title']}")
        logger.info(f"  Status Code: {result['result']['status']}")
        logger.info(f"  Execution Time: {result['execution_time']:.2f}s")
    else:
        logger.error(f"✗ Navigation failed: {result['error']}")


async def example_2_screenshot_capture():
    """Example 2: Capture screenshots."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 2: Screenshot Capture")
    logger.info("=" * 80)

    tool = create_browser_automation_tool()

    if not tool.is_available():
        logger.error("Playwright not installed.")
        return

    # Navigate first
    await tool.execute(action='navigate', url='https://example.com')

    # Create screenshots directory
    screenshots_dir = Path('E:/screenshots')
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Take screenshot
    screenshot_path = screenshots_dir / 'example_page.png'
    result = await tool.execute(
        action='screenshot',
        path=str(screenshot_path)
    )

    if result['success']:
        logger.info(f"✓ Screenshot captured")
        logger.info(f"  Path: {result['result']['path']}")
        logger.info(f"  Size: {result['result']['size_bytes']} bytes")
    else:
        logger.error(f"✗ Screenshot failed: {result['error']}")


async def example_3_text_extraction():
    """Example 3: Extract text content from web pages."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 3: Text Extraction")
    logger.info("=" * 80)

    tool = create_browser_automation_tool()

    if not tool.is_available():
        logger.error("Playwright not installed.")
        return

    # Navigate to page
    await tool.execute(action='navigate', url='https://example.com')

    # Extract text from specific element
    result = await tool.execute(
        action='get_text',
        selector='h1'  # Get the main heading
    )

    if result['success']:
        logger.info(f"✓ Text extracted")
        logger.info(f"  Selector: {result['result']['selector']}")
        logger.info(f"  Text: {result['result']['text']}")
        logger.info(f"  Length: {result['result']['length']} characters")
    else:
        logger.error(f"✗ Text extraction failed: {result['error']}")


async def example_4_form_automation():
    """Example 4: Automate form filling."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 4: Form Automation")
    logger.info("=" * 80)

    tool = create_browser_automation_tool()

    if not tool.is_available():
        logger.error("Playwright not installed.")
        return

    # Navigate to a form page (hypothetical example)
    await tool.execute(action='navigate', url='https://httpbin.org/forms/post')

    # Fill in form fields
    result_email = await tool.execute(
        action='fill',
        selector='input[name="custname"]',
        text='John Doe'
    )

    if result_email['success']:
        logger.info(f"✓ Form field filled: {result_email['result']['selector']}")
    else:
        logger.error(f"✗ Form fill failed: {result_email['error']}")


async def example_5_click_interactions():
    """Example 5: Click buttons and links."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 5: Click Interactions")
    logger.info("=" * 80)

    tool = create_browser_automation_tool()

    if not tool.is_available():
        logger.error("Playwright not installed.")
        return

    # Navigate to page
    await tool.execute(action='navigate', url='https://example.com')

    # Click a link (hypothetical selector)
    result = await tool.execute(
        action='click',
        selector='a[href]'  # Click first link
    )

    if result['success']:
        logger.info(f"✓ Element clicked: {result['result']['selector']}")
    else:
        logger.error(f"✗ Click failed: {result['error']}")


async def example_6_wait_for_elements():
    """Example 6: Wait for dynamic content."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 6: Wait for Dynamic Content")
    logger.info("=" * 80)

    tool = create_browser_automation_tool()

    if not tool.is_available():
        logger.error("Playwright not installed.")
        return

    # Navigate to page with dynamic content
    await tool.execute(action='navigate', url='https://example.com')

    # Wait for element to appear
    result = await tool.execute(
        action='wait_for',
        selector='h1',
        timeout_ms=5000  # Wait up to 5 seconds
    )

    if result['success']:
        logger.info(f"✓ Element found: {result['result']['selector']}")
    else:
        logger.error(f"✗ Wait timeout: {result['error']}")


async def example_7_javascript_execution():
    """Example 7: Execute JavaScript in browser."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 7: JavaScript Execution")
    logger.info("=" * 80)

    tool = create_browser_automation_tool()

    if not tool.is_available():
        logger.error("Playwright not installed.")
        return

    # Navigate to page
    await tool.execute(action='navigate', url='https://example.com')

    # Execute JavaScript to get page info
    result = await tool.execute(
        action='evaluate',
        javascript='document.title'
    )

    if result['success']:
        logger.info(f"✓ JavaScript executed")
        logger.info(f"  Output: {result['result']['output']}")
    else:
        logger.error(f"✗ JavaScript execution failed: {result['error']}")

    # Execute more complex JavaScript
    result = await tool.execute(
        action='evaluate',
        javascript='document.querySelectorAll("a").length'
    )

    if result['success']:
        logger.info(f"✓ Link count: {result['result']['output']}")


async def example_8_custom_configuration():
    """Example 8: Use custom browser configuration."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 8: Custom Browser Configuration")
    logger.info("=" * 80)

    # Create tool with custom settings
    tool = create_browser_automation_tool(
        headless=False,  # Run with visible browser
        browser_type='firefox',  # Use Firefox instead of Chromium
        timeout=60000,  # 60 second timeout
        viewport_width=1920,  # Full HD width
        viewport_height=1080  # Full HD height
    )

    if not tool.is_available():
        logger.error("Playwright not installed.")
        return

    logger.info(f"Browser Type: {tool.browser_type}")
    logger.info(f"Headless Mode: {tool.headless}")
    logger.info(f"Viewport: {tool.viewport_width}x{tool.viewport_height}")
    logger.info(f"Timeout: {tool.timeout}ms")

    # Use the custom configured tool
    result = await tool.execute(action='navigate', url='https://example.com')

    if result['success']:
        logger.info(f"✓ Navigation with custom config successful")
    else:
        logger.error(f"✗ Navigation failed: {result['error']}")


async def example_9_complete_workflow():
    """Example 9: Complete automation workflow."""
    from torq_console.agents.tools import create_browser_automation_tool

    logger.info("=" * 80)
    logger.info("Example 9: Complete Automation Workflow")
    logger.info("=" * 80)

    tool = create_browser_automation_tool()

    if not tool.is_available():
        logger.error("Playwright not installed.")
        return

    # Step 1: Navigate
    logger.info("Step 1: Navigate to website")
    result = await tool.execute(action='navigate', url='https://example.com')
    if not result['success']:
        logger.error(f"Navigation failed: {result['error']}")
        return

    # Step 2: Wait for content
    logger.info("Step 2: Wait for content to load")
    result = await tool.execute(action='wait_for', selector='h1', timeout_ms=5000)
    if not result['success']:
        logger.error(f"Content load timeout: {result['error']}")
        return

    # Step 3: Extract data
    logger.info("Step 3: Extract page title")
    result = await tool.execute(action='get_text', selector='h1')
    if result['success']:
        page_title = result['result']['text']
        logger.info(f"  Page title: {page_title}")

    # Step 4: Get additional info via JavaScript
    logger.info("Step 4: Execute JavaScript")
    result = await tool.execute(action='evaluate', javascript='window.location.href')
    if result['success']:
        current_url = result['result']['output']
        logger.info(f"  Current URL: {current_url}")

    # Step 5: Take screenshot
    logger.info("Step 5: Capture screenshot")
    screenshots_dir = Path('E:/screenshots')
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshots_dir / 'workflow_result.png'

    result = await tool.execute(action='screenshot', path=str(screenshot_path))
    if result['success']:
        logger.info(f"  Screenshot saved: {result['result']['path']}")

    logger.info("✓ Complete workflow finished successfully!")


async def example_10_prince_integration():
    """Example 10: Use browser automation through Prince Flowers agent."""
    from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

    logger.info("=" * 80)
    logger.info("Example 10: Prince Flowers Integration")
    logger.info("=" * 80)

    # Create Prince Flowers agent
    prince = TORQPrinceFlowers()

    # Check if browser automation is available
    if 'browser_automation' in prince.available_tools:
        logger.info("✓ Browser automation available in Prince's toolkit")
        tool_info = prince.available_tools['browser_automation']
        logger.info(f"  Name: {tool_info['name']}")
        logger.info(f"  Description: {tool_info['description']}")
        logger.info(f"  Cost: {tool_info['cost']}")
        logger.info(f"  Success Rate: {tool_info['success_rate']}")
    else:
        logger.error("✗ Browser automation not registered with Prince")

    # Note: To execute via Prince, you would need to call:
    # result = await prince._execute_browser_automation(action='navigate', url='https://example.com')


async def run_all_examples():
    """Run all usage examples."""
    logger.info("=" * 80)
    logger.info("Browser Automation Tool - Usage Examples")
    logger.info("=" * 80)

    try:
        await example_1_basic_navigation()
        await asyncio.sleep(1)

        await example_2_screenshot_capture()
        await asyncio.sleep(1)

        await example_3_text_extraction()
        await asyncio.sleep(1)

        await example_4_form_automation()
        await asyncio.sleep(1)

        await example_5_click_interactions()
        await asyncio.sleep(1)

        await example_6_wait_for_elements()
        await asyncio.sleep(1)

        await example_7_javascript_execution()
        await asyncio.sleep(1)

        await example_8_custom_configuration()
        await asyncio.sleep(1)

        await example_9_complete_workflow()
        await asyncio.sleep(1)

        await example_10_prince_integration()

        logger.info("=" * 80)
        logger.info("✓ All examples completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error running examples: {e}")


if __name__ == '__main__':
    # Run all examples
    asyncio.run(run_all_examples())
