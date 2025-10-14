"""
Browser Automation Tool for Prince Flowers
Provides browser automation capabilities using Playwright for web interactions, testing, and scraping
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# Try to import playwright for async browser automation
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not installed. Install with: pip install playwright && playwright install")


class BrowserAutomationTool:
    """
    Prince Flowers tool wrapper for browser automation using Playwright.

    Provides a standardized interface for browser interactions including:
    - Web page navigation and interaction
    - Element clicking and form filling
    - Screenshot capture
    - Text content extraction
    - JavaScript execution
    - Element waiting and synchronization

    Supports:
    - Headless and headed browser modes
    - Automatic browser cleanup
    - Error handling with actionable messages
    - Multiple browser engines (Chromium, Firefox, WebKit)

    Example:
        >>> tool = create_browser_automation_tool()
        >>> result = await tool.execute(
        ...     action='navigate',
        ...     url='https://example.com'
        ... )
        >>> print(result['success'])
        True
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = 'chromium',
        timeout: int = 30000,
        viewport_width: int = 1280,
        viewport_height: int = 720
    ):
        """
        Initialize the Browser Automation Tool.

        Args:
            headless: Run browser in headless mode (default: True)
            browser_type: Browser engine to use ('chromium', 'firefox', 'webkit')
            timeout: Default timeout for operations in milliseconds (default: 30000)
            viewport_width: Browser viewport width in pixels (default: 1280)
            viewport_height: Browser viewport height in pixels (default: 720)
        """
        self.logger = logging.getLogger(__name__)

        # Tool metadata for Prince's ecosystem
        self.name = "Browser Automation"
        self.description = "Automate web browser interactions using Playwright"
        self.cost = 0.4  # Time/resource cost for RL system
        self.success_rate = 0.85  # Historical success rate
        self.avg_time = 2.5  # Average execution time in seconds
        self.requires_approval = False  # No approval needed for browser automation
        self.composable = True  # Can be composed with other tools

        # Configuration from parameters or environment
        self.headless = headless if os.getenv('BROWSER_HEADLESS') is None else os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
        self.browser_type = os.getenv('BROWSER_TYPE', browser_type).lower()
        self.timeout = int(os.getenv('BROWSER_TIMEOUT', str(timeout)))
        self.viewport_width = int(os.getenv('BROWSER_VIEWPORT_WIDTH', str(viewport_width)))
        self.viewport_height = int(os.getenv('BROWSER_VIEWPORT_HEIGHT', str(viewport_height)))

        # Validate browser type
        if self.browser_type not in ['chromium', 'firefox', 'webkit']:
            self.logger.warning(f"Invalid browser type '{self.browser_type}', defaulting to 'chromium'")
            self.browser_type = 'chromium'

        # Browser instances (managed per-execution)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Availability check
        self.configured = PLAYWRIGHT_AVAILABLE

        if self.configured:
            self.logger.info(f"Browser Automation Tool initialized successfully (headless={self.headless}, browser={self.browser_type})")
        else:
            self.logger.warning("Browser Automation Tool not available - Playwright not installed")

    def is_available(self) -> bool:
        """
        Check if the tool is available and configured.

        Returns:
            True if Playwright is installed and configured, False otherwise
        """
        return self.configured

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        javascript: Optional[str] = None,
        path: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute browser automation operations.

        Args:
            action: Operation to perform
                - 'navigate': Navigate to URL (requires url)
                - 'click': Click element (requires selector)
                - 'fill': Fill input field (requires selector, text)
                - 'screenshot': Take screenshot (requires path)
                - 'get_text': Extract text content (requires selector)
                - 'wait_for': Wait for element (requires selector)
                - 'evaluate': Execute JavaScript (requires javascript)
            url: Target URL for navigation
            selector: CSS selector for element operations
            text: Text content for fill operations
            javascript: JavaScript code to execute
            path: File path for screenshot output
            timeout_ms: Operation timeout in milliseconds (overrides default)
            **kwargs: Additional parameters for specific actions

        Returns:
            Dict containing:
                - success: bool - Operation success status
                - result: Any - Operation result data
                - error: str - Error message (if failed)
                - execution_time: float - Operation duration in seconds
                - timestamp: str - ISO format timestamp

        Example:
            >>> # Navigate to URL
            >>> result = await tool.execute(action='navigate', url='https://example.com')
            >>>
            >>> # Click element
            >>> result = await tool.execute(action='click', selector='button#submit')
            >>>
            >>> # Fill form field
            >>> result = await tool.execute(
            ...     action='fill',
            ...     selector='input[name="email"]',
            ...     text='user@example.com'
            ... )
            >>>
            >>> # Take screenshot
            >>> result = await tool.execute(
            ...     action='screenshot',
            ...     path='E:/screenshots/page.png'
            ... )
            >>>
            >>> # Get text content
            >>> result = await tool.execute(
            ...     action='get_text',
            ...     selector='h1.title'
            ... )
            >>>
            >>> # Wait for element
            >>> result = await tool.execute(
            ...     action='wait_for',
            ...     selector='div.loaded',
            ...     timeout_ms=5000
            ... )
            >>>
            >>> # Execute JavaScript
            >>> result = await tool.execute(
            ...     action='evaluate',
            ...     javascript='document.title'
            ... )
        """
        start_time = datetime.now()

        # Validate availability
        if not self.is_available():
            error_msg = self._get_unavailable_error_message()
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }

        # Use custom timeout or default
        operation_timeout = timeout_ms if timeout_ms is not None else self.timeout

        # Route to appropriate handler
        try:
            # Initialize browser if needed (for first operation)
            await self._ensure_browser_ready()

            if action == 'navigate':
                if not url:
                    raise ValueError("url is required for navigate action")
                result = await self._navigate(url, operation_timeout)
            elif action == 'click':
                if not selector:
                    raise ValueError("selector is required for click action")
                result = await self._click(selector, operation_timeout)
            elif action == 'fill':
                if not selector or text is None:
                    raise ValueError("selector and text are required for fill action")
                result = await self._fill(selector, text, operation_timeout)
            elif action == 'screenshot':
                if not path:
                    raise ValueError("path is required for screenshot action")
                result = await self._screenshot(path, operation_timeout)
            elif action == 'get_text':
                if not selector:
                    raise ValueError("selector is required for get_text action")
                result = await self._get_text(selector, operation_timeout)
            elif action == 'wait_for':
                if not selector:
                    raise ValueError("selector is required for wait_for action")
                result = await self._wait_for(selector, operation_timeout)
            elif action == 'evaluate':
                if not javascript:
                    raise ValueError("javascript is required for evaluate action")
                result = await self._evaluate(javascript, operation_timeout)
            else:
                raise ValueError(
                    f"Unknown action: {action}. Valid actions: navigate, click, fill, "
                    f"screenshot, get_text, wait_for, evaluate"
                )

            # Add execution metadata
            result['execution_time'] = (datetime.now() - start_time).total_seconds()
            result['timestamp'] = datetime.now().isoformat()

            if result.get('success'):
                self.logger.info(f"Browser {action} completed successfully")
            else:
                self.logger.warning(f"Browser {action} failed: {result.get('error')}")

            return result

        except ValueError as e:
            error_msg = f"Validation error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Unexpected error during {action}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            # Cleanup browser resources after operation
            await self._cleanup_browser()

    async def _ensure_browser_ready(self):
        """
        Ensure browser is initialized and ready for operations.

        Raises:
            Exception: If browser initialization fails
        """
        if self.page is not None:
            return  # Already initialized

        try:
            self.logger.info(f"Initializing {self.browser_type} browser (headless={self.headless})")

            # Start playwright
            self.playwright = await async_playwright().start()

            # Launch browser based on type
            if self.browser_type == 'chromium':
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == 'firefox':
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == 'webkit':
                self.browser = await self.playwright.webkit.launch(headless=self.headless)

            # Create context with viewport
            self.context = await self.browser.new_context(
                viewport={'width': self.viewport_width, 'height': self.viewport_height}
            )

            # Create page
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)

            self.logger.info("Browser initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            await self._cleanup_browser()
            raise

    async def _cleanup_browser(self):
        """Cleanup browser resources."""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self.logger.debug("Browser resources cleaned up")

        except Exception as e:
            self.logger.error(f"Error during browser cleanup: {e}")

    async def _navigate(self, url: str, timeout: int) -> Dict[str, Any]:
        """
        Navigate to URL.

        Args:
            url: Target URL
            timeout: Navigation timeout in milliseconds

        Returns:
            Dict with success status and navigation result
        """
        try:
            response = await self.page.goto(url, timeout=timeout, wait_until='domcontentloaded')

            return {
                'success': True,
                'result': {
                    'url': url,
                    'final_url': self.page.url,
                    'status': response.status if response else None,
                    'title': await self.page.title()
                },
                'error': None
            }

        except PlaywrightTimeoutError as e:
            error_msg = f"Navigation timeout after {timeout}ms: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Navigation error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _click(self, selector: str, timeout: int) -> Dict[str, Any]:
        """
        Click element.

        Args:
            selector: CSS selector for element
            timeout: Click timeout in milliseconds

        Returns:
            Dict with success status and click result
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector, timeout=timeout)

            return {
                'success': True,
                'result': {
                    'selector': selector,
                    'clicked': True
                },
                'error': None
            }

        except PlaywrightTimeoutError as e:
            error_msg = f"Click timeout - element not found or not clickable: {selector}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Click error on selector '{selector}': {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _fill(self, selector: str, text: str, timeout: int) -> Dict[str, Any]:
        """
        Fill input field.

        Args:
            selector: CSS selector for input element
            text: Text to fill
            timeout: Fill timeout in milliseconds

        Returns:
            Dict with success status and fill result
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.fill(selector, text, timeout=timeout)

            return {
                'success': True,
                'result': {
                    'selector': selector,
                    'text': text,
                    'filled': True
                },
                'error': None
            }

        except PlaywrightTimeoutError as e:
            error_msg = f"Fill timeout - element not found: {selector}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Fill error on selector '{selector}': {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _screenshot(self, path: str, timeout: int) -> Dict[str, Any]:
        """
        Take screenshot.

        Args:
            path: File path for screenshot output
            timeout: Screenshot timeout in milliseconds

        Returns:
            Dict with success status and screenshot path
        """
        try:
            # Ensure directory exists
            screenshot_path = Path(path)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)

            # Take screenshot
            await self.page.screenshot(path=str(screenshot_path), timeout=timeout)

            return {
                'success': True,
                'result': {
                    'path': str(screenshot_path.resolve()),
                    'exists': screenshot_path.exists(),
                    'size_bytes': screenshot_path.stat().st_size if screenshot_path.exists() else 0
                },
                'error': None
            }

        except Exception as e:
            error_msg = f"Screenshot error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _get_text(self, selector: str, timeout: int) -> Dict[str, Any]:
        """
        Extract text content.

        Args:
            selector: CSS selector for element
            timeout: Wait timeout in milliseconds

        Returns:
            Dict with success status and text content
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            text_content = await self.page.text_content(selector, timeout=timeout)

            return {
                'success': True,
                'result': {
                    'selector': selector,
                    'text': text_content,
                    'length': len(text_content) if text_content else 0
                },
                'error': None
            }

        except PlaywrightTimeoutError as e:
            error_msg = f"Get text timeout - element not found: {selector}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Get text error on selector '{selector}': {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _wait_for(self, selector: str, timeout: int) -> Dict[str, Any]:
        """
        Wait for element.

        Args:
            selector: CSS selector for element
            timeout: Wait timeout in milliseconds

        Returns:
            Dict with success status and wait result
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)

            return {
                'success': True,
                'result': {
                    'selector': selector,
                    'found': True
                },
                'error': None
            }

        except PlaywrightTimeoutError as e:
            error_msg = f"Wait timeout - element not found: {selector}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Wait error for selector '{selector}': {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _evaluate(self, javascript: str, timeout: int) -> Dict[str, Any]:
        """
        Execute JavaScript.

        Args:
            javascript: JavaScript code to execute
            timeout: Execution timeout in milliseconds

        Returns:
            Dict with success status and evaluation result
        """
        try:
            result = await self.page.evaluate(javascript, timeout=timeout)

            return {
                'success': True,
                'result': {
                    'javascript': javascript,
                    'output': result
                },
                'error': None
            }

        except PlaywrightTimeoutError as e:
            error_msg = f"JavaScript execution timeout: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"JavaScript execution error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    def _get_unavailable_error_message(self) -> str:
        """
        Generate detailed error message when tool is unavailable.

        Returns:
            Actionable error message string
        """
        error_msg = "Browser Automation Tool not available. "

        if not PLAYWRIGHT_AVAILABLE:
            error_msg += "Missing dependency: Playwright. Install with: pip install playwright && playwright install"

        return error_msg

    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get tool information for Prince's tool registry.

        Returns:
            Dict containing tool metadata including parameters and capabilities
        """
        return {
            'name': self.name,
            'description': self.description,
            'cost': self.cost,
            'success_rate': self.success_rate,
            'avg_time': self.avg_time,
            'requires_approval': self.requires_approval,
            'composable': self.composable,
            'available': self.is_available(),
            'dependencies': ['playwright'],
            'browser_type': self.browser_type,
            'headless': self.headless,
            'parameters': {
                'action': {
                    'type': 'string',
                    'required': True,
                    'enum': ['navigate', 'click', 'fill', 'screenshot', 'get_text', 'wait_for', 'evaluate'],
                    'description': 'Browser operation to perform'
                },
                'url': {
                    'type': 'string',
                    'required': False,
                    'description': 'Target URL (required for navigate)'
                },
                'selector': {
                    'type': 'string',
                    'required': False,
                    'description': 'CSS selector (required for click, fill, get_text, wait_for)'
                },
                'text': {
                    'type': 'string',
                    'required': False,
                    'description': 'Text content (required for fill)'
                },
                'javascript': {
                    'type': 'string',
                    'required': False,
                    'description': 'JavaScript code (required for evaluate)'
                },
                'path': {
                    'type': 'string',
                    'required': False,
                    'description': 'File path (required for screenshot)'
                },
                'timeout_ms': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Operation timeout in milliseconds'
                }
            }
        }

    def format_for_prince(self, result: Dict[str, Any]) -> str:
        """
        Format result for Prince Flowers output.

        Args:
            result: Execution result dict

        Returns:
            Formatted string for Prince's response
        """
        if not result.get('success'):
            return f"Browser automation failed: {result.get('error', 'Unknown error')}"

        result_data = result.get('result', {})

        # Format based on result type
        if 'url' in result_data:
            # Navigation result
            response = f"Browser Navigation:\n\n"
            response += f"URL: {result_data.get('url')}\n"
            response += f"Final URL: {result_data.get('final_url')}\n"
            response += f"Status: {result_data.get('status')}\n"
            response += f"Title: {result_data.get('title')}\n"
            return response

        elif 'clicked' in result_data:
            # Click result
            return f"Clicked element: {result_data.get('selector')}"

        elif 'filled' in result_data:
            # Fill result
            return f"Filled element: {result_data.get('selector')} with text (length: {len(result_data.get('text', ''))})"

        elif 'path' in result_data:
            # Screenshot result
            response = f"Screenshot captured:\n\n"
            response += f"Path: {result_data.get('path')}\n"
            response += f"Size: {result_data.get('size_bytes', 0)} bytes\n"
            return response

        elif 'text' in result_data:
            # Get text result
            text = result_data.get('text', '')
            preview = text[:200] + '...' if len(text) > 200 else text
            response = f"Text content (length: {result_data.get('length', 0)}):\n\n"
            response += f"{preview}\n"
            return response

        elif 'found' in result_data:
            # Wait result
            return f"Element found: {result_data.get('selector')}"

        elif 'output' in result_data:
            # JavaScript evaluation result
            output = str(result_data.get('output', ''))
            response = f"JavaScript execution result:\n\n"
            response += f"{output[:500]}\n"
            return response

        else:
            # Generic result
            return f"Browser operation completed successfully:\n{result_data}"


# Factory function for easy integration
def create_browser_automation_tool(
    headless: bool = True,
    browser_type: str = 'chromium',
    timeout: int = 30000,
    viewport_width: int = 1280,
    viewport_height: int = 720
) -> BrowserAutomationTool:
    """
    Factory function to create Browser Automation tool instance.

    Args:
        headless: Run browser in headless mode (default: True)
        browser_type: Browser engine ('chromium', 'firefox', 'webkit')
        timeout: Default timeout in milliseconds (default: 30000)
        viewport_width: Browser viewport width in pixels (default: 1280)
        viewport_height: Browser viewport height in pixels (default: 720)

    Returns:
        BrowserAutomationTool instance

    Example:
        >>> # Using defaults (headless chromium)
        >>> tool = create_browser_automation_tool()
        >>>
        >>> # Using headed Firefox
        >>> tool = create_browser_automation_tool(
        ...     headless=False,
        ...     browser_type='firefox'
        ... )
        >>>
        >>> # Custom configuration
        >>> tool = create_browser_automation_tool(
        ...     headless=True,
        ...     browser_type='chromium',
        ...     timeout=60000,
        ...     viewport_width=1920,
        ...     viewport_height=1080
        ... )
    """
    return BrowserAutomationTool(
        headless=headless,
        browser_type=browser_type,
        timeout=timeout,
        viewport_width=viewport_width,
        viewport_height=viewport_height
    )
