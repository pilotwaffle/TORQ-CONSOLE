"""
Automation Tools Module - Consolidated Browser and Workflow Automation

This module consolidates browser_automation_tool.py and multi_tool_composition_tool.py
into a unified automation framework.

Provides workflow automation and orchestration capabilities:
- Browser automation via Playwright
- Multi-tool workflow orchestration
- Sequential/parallel/conditional execution patterns
- Data transformation and aggregation
- Web scraping and interaction

Author: TORQ Console Development Team
Version: 2.0.0 (Consolidated)
"""

import logging
import asyncio
import time
import re
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from copy import deepcopy

# Try to import playwright for browser automation
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not installed. Browser automation unavailable. Install with: pip install playwright && playwright install")

logger = logging.getLogger(__name__)


class BrowserEngine(Enum):
    """Supported browser engines."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class WorkflowType(Enum):
    """Supported workflow composition patterns."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    MAP_REDUCE = "map_reduce"
    PIPELINE = "pipeline"


class ErrorStrategy(Enum):
    """Error handling strategies for workflow steps."""
    CONTINUE = "continue"  # Continue to next step
    STOP = "stop"  # Stop workflow execution
    ROLLBACK = "rollback"  # Rollback all completed steps
    RETRY = "retry"  # Retry the failed step


class AutomationStatus(Enum):
    """Automation task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BrowserAction:
    """Definition of a browser automation action."""
    action_type: str  # navigate, click, fill_text, screenshot, etc.
    selector: Optional[str] = None  # CSS selector or XPath
    value: Optional[str] = None  # Value to input or action parameter
    options: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30000  # Timeout in milliseconds


@dataclass
class WorkflowStep:
    """Single step in a workflow."""
    step_name: str
    step_type: str  # tool, browser, condition, etc.
    tool_name: Optional[str] = None
    action: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None  # For conditional steps
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    name: str
    description: str
    workflow_type: WorkflowType
    steps: List[WorkflowStep]
    error_strategy: ErrorStrategy = ErrorStrategy.STOP
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of a single workflow step execution."""
    step_name: str
    step_type: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_name: str
    success: bool
    steps_completed: int
    total_steps: int
    results: List[StepResult] = field(default_factory=list)
    final_result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    status: AutomationStatus = AutomationStatus.COMPLETED
    timestamp: datetime = field(default_factory=datetime.now)


class AutomationError(Exception):
    """Base exception for automation errors."""
    pass


class BrowserAutomationError(AutomationError):
    """Browser automation specific errors."""
    pass


class WorkflowExecutionError(AutomationError):
    """Workflow execution specific errors."""
    pass


class BaseAutomationTool(ABC):
    """Base class for automation tools."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"torq.automation.{name}")

    @abstractmethod
    async def execute(self, action: str, **kwargs) -> Any:
        """Execute automation action."""
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup resources."""
        pass


class BrowserAutomationTool(BaseAutomationTool):
    """Advanced browser automation using Playwright."""

    def __init__(
        self,
        browser_engine: BrowserEngine = BrowserEngine.CHROMIUM,
        headless: bool = True,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None
    ):
        super().__init__("browser_automation")

        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for browser automation")

        self.browser_engine = browser_engine
        self.headless = headless
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.user_agent = user_agent

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize(self) -> bool:
        """Initialize browser and context."""
        try:
            self.playwright = await async_playwright().start()

            launch_options = {
                "headless": self.headless,
            }

            # Launch browser based on engine
            if self.browser_engine == BrowserEngine.CHROMIUM:
                self.browser = await self.playwright.chromium.launch(**launch_options)
            elif self.browser_engine == BrowserEngine.FIREFOX:
                self.browser = await self.playwright.firefox.launch(**launch_options)
            elif self.browser_engine == BrowserEngine.WEBKIT:
                self.browser = await self.playwright.webkit.launch(**launch_options)

            # Create context
            context_options = {
                "viewport": self.viewport,
                "ignore_https_errors": True,
            }

            if self.user_agent:
                context_options["user_agent"] = self.user_agent

            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()

            self.logger.info(f"Browser initialized: {self.browser_engine.value}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False

    async def execute(self, action: str, **kwargs) -> Any:
        """Execute browser action."""
        if not self.page:
            if not await self.initialize():
                raise BrowserAutomationError("Failed to initialize browser")

        try:
            if action == "navigate":
                return await self._navigate(kwargs.get("url"))
            elif action == "click":
                return await self._click(kwargs.get("selector"), kwargs.get("options", {}))
            elif action == "fill_text":
                return await self._fill_text(kwargs.get("selector"), kwargs.get("text"))
            elif action == "screenshot":
                return await self._screenshot(kwargs.get("path"))
            elif action == "get_text":
                return await self._get_text(kwargs.get("selector"))
            elif action == "wait_for_element":
                return await self._wait_for_element(kwargs.get("selector"), kwargs.get("timeout", 30000))
            elif action == "execute_script":
                return await self._execute_script(kwargs.get("script"))
            elif action == "scroll":
                return await self._scroll(kwargs.get("direction", "down"))
            else:
                raise BrowserAutomationError(f"Unknown browser action: {action}")

        except PlaywrightTimeoutError:
            raise BrowserAutomationError(f"Browser action timed out: {action}")
        except Exception as e:
            raise BrowserAutomationError(f"Browser action failed: {action} - {str(e)}")

    async def _navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL."""
        if not url:
            raise BrowserAutomationError("URL is required for navigation")

        start_time = time.time()
        response = await self.page.goto(url, wait_until="networkidle")
        execution_time = time.time() - start_time

        return {
            "success": response is not None,
            "url": self.page.url,
            "title": await self.page.title(),
            "status": response.status if response else None,
            "execution_time": execution_time
        }

    async def _click(self, selector: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Click on element."""
        if not selector:
            raise BrowserAutomationError("Selector is required for click")

        start_time = time.time()

        # Wait for element to be visible and clickable
        await self.page.wait_for_selector(selector, state="visible")
        await self.page.click(selector, **options)

        execution_time = time.time() - start_time

        return {
            "success": True,
            "selector": selector,
            "execution_time": execution_time
        }

    async def _fill_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Fill text input field."""
        if not selector or text is None:
            raise BrowserAutomationError("Selector and text are required for fill_text")

        start_time = time.time()

        # Wait for element and fill text
        await self.page.wait_for_selector(selector)
        await self.page.fill(selector, text)

        execution_time = time.time() - start_time

        return {
            "success": True,
            "selector": selector,
            "text_length": len(text),
            "execution_time": execution_time
        }

    async def _screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Take screenshot."""
        start_time = time.time()

        screenshot_bytes = await self.page.screenshot(full_page=True, type="png")

        if path:
            with open(path, "wb") as f:
                f.write(screenshot_bytes)

        execution_time = time.time() - start_time

        return {
            "success": True,
            "path": path,
            "size": len(screenshot_bytes),
            "execution_time": execution_time
        }

    async def _get_text(self, selector: str) -> Dict[str, Any]:
        """Get text content of element."""
        if not selector:
            raise BrowserAutomationError("Selector is required for get_text")

        start_time = time.time()

        element = await self.page.wait_for_selector(selector)
        text = await element.text_content()

        execution_time = time.time() - start_time

        return {
            "success": True,
            "selector": selector,
            "text": text,
            "execution_time": execution_time
        }

    async def _wait_for_element(self, selector: str, timeout: int) -> Dict[str, Any]:
        """Wait for element to appear."""
        if not selector:
            raise BrowserAutomationError("Selector is required for wait_for_element")

        start_time = time.time()

        await self.page.wait_for_selector(selector, timeout=timeout)

        execution_time = time.time() - start_time

        return {
            "success": True,
            "selector": selector,
            "execution_time": execution_time
        }

    async def _execute_script(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript in browser context."""
        if not script:
            raise BrowserAutomationError("Script is required for execute_script")

        start_time = time.time()

        result = await self.page.evaluate(script)

        execution_time = time.time() - start_time

        return {
            "success": True,
            "result": result,
            "execution_time": execution_time
        }

    async def _scroll(self, direction: str) -> Dict[str, Any]:
        """Scroll page in specified direction."""
        start_time = time.time()

        if direction == "down":
            await self.page.keyboard.press("PageDown")
        elif direction == "up":
            await self.page.keyboard.press("PageUp")
        elif direction == "top":
            await self.page.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Wait a moment for scroll to complete
        await asyncio.sleep(0.5)

        execution_time = time.time() - start_time

        return {
            "success": True,
            "direction": direction,
            "execution_time": execution_time
        }

    async def cleanup(self):
        """Close browser and cleanup resources."""
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

        except Exception as e:
            self.logger.error(f"Error during browser cleanup: {e}")


class WorkflowOrchestrator(BaseAutomationTool):
    """Advanced workflow orchestration with multiple execution patterns."""

    def __init__(self, tool_registry: Optional[Dict[str, BaseAutomationTool]] = None):
        super().__init__("workflow_orchestrator")
        self.tool_registry = tool_registry or {}
        self.active_workflows: Dict[str, WorkflowResult] = {}

    def register_tool(self, name: str, tool: BaseAutomationTool):
        """Register a tool for use in workflows."""
        self.tool_registry[name] = tool
        self.logger.info(f"Registered tool: {name}")

    async def execute(self, action: str, **kwargs) -> Any:
        """Execute workflow action."""
        if action == "run_workflow":
            return await self.run_workflow(kwargs.get("workflow"))
        elif action == "run_step":
            return await self.run_step(kwargs.get("step"))
        else:
            raise WorkflowExecutionError(f"Unknown workflow action: {action}")

    async def run_workflow(self, workflow: WorkflowDefinition) -> WorkflowResult:
        """Execute a complete workflow."""
        start_time = time.time()
        self.logger.info(f"Starting workflow: {workflow.name}")

        try:
            workflow_result = WorkflowResult(
                workflow_name=workflow.name,
                success=False,
                steps_completed=0,
                total_steps=len(workflow.steps),
                status=AutomationStatus.RUNNING
            )

            self.active_workflows[workflow.name] = workflow_result

            if workflow.workflow_type == WorkflowType.SEQUENTIAL:
                workflow_result = await self._run_sequential(workflow, workflow_result)
            elif workflow.workflow_type == WorkflowType.PARALLEL:
                workflow_result = await self._run_parallel(workflow, workflow_result)
            elif workflow.workflow_type == WorkflowType.CONDITIONAL:
                workflow_result = await self._run_conditional(workflow, workflow_result)
            elif workflow.workflow_type == WorkflowType.LOOP:
                workflow_result = await self._run_loop(workflow, workflow_result)
            elif workflow.workflow_type == WorkflowType.PIPELINE:
                workflow_result = await self._run_pipeline(workflow, workflow_result)
            else:
                raise WorkflowExecutionError(f"Unsupported workflow type: {workflow.workflow_type}")

            workflow_result.execution_time = time.time() - start_time
            workflow_result.status = AutomationStatus.COMPLETED if workflow_result.success else AutomationStatus.FAILED

            self.logger.info(f"Workflow {workflow.name} completed in {workflow_result.execution_time:.2f}s")
            return workflow_result

        except Exception as e:
            workflow_result.execution_time = time.time() - start_time
            workflow_result.error = str(e)
            workflow_result.status = AutomationStatus.FAILED
            self.logger.error(f"Workflow {workflow.name} failed: {e}")
            return workflow_result

        finally:
            if workflow.name in self.active_workflows:
                del self.active_workflows[workflow.name]

    async def _run_sequential(self, workflow: WorkflowDefinition, workflow_result: WorkflowResult) -> WorkflowResult:
        """Execute workflow steps sequentially."""
        for i, step in enumerate(workflow.steps):
            try:
                step_result = await self.run_step(step)
                workflow_result.results.append(step_result)

                if not step_result.success:
                    self.logger.error(f"Step {step.step_name} failed: {step_result.error}")

                    if workflow.error_strategy == ErrorStrategy.STOP:
                        workflow_result.success = False
                        workflow_result.error = f"Step {step.step_name} failed: {step_result.error}"
                        return workflow_result
                    elif workflow.error_strategy == ErrorStrategy.CONTINUE:
                        continue  # Continue to next step

                workflow_result.steps_completed = i + 1

            except Exception as e:
                self.logger.error(f"Exception in step {step.step_name}: {e}")
                workflow_result.success = False
                workflow_result.error = f"Exception in step {step.step_name}: {str(e)}"
                return workflow_result

        workflow_result.success = True
        return workflow_result

    async def _run_parallel(self, workflow: WorkflowDefinition, workflow_result: WorkflowResult) -> WorkflowResult:
        """Execute workflow steps in parallel."""
        tasks = []
        for step in workflow.steps:
            task = asyncio.create_task(self.run_step(step))
            tasks.append(task)

        try:
            step_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, step_result in enumerate(step_results):
                if isinstance(step_result, Exception):
                    workflow_result.results.append(StepResult(
                        step_name=workflow.steps[i].step_name,
                        step_type=workflow.steps[i].step_type,
                        success=False,
                        error=str(step_result)
                    ))
                    workflow_result.success = False
                    workflow_result.error = f"Parallel step failed: {str(step_result)}"
                else:
                    workflow_result.results.append(step_result)
                    if not step_result.success and workflow_result.success:
                        workflow_result.success = False

            workflow_result.steps_completed = len(workflow.steps)

        except Exception as e:
            workflow_result.success = False
            workflow_result.error = f"Parallel execution failed: {str(e)}"

        return workflow_result

    async def _run_conditional(self, workflow: WorkflowDefinition, workflow_result: WorkflowResult) -> WorkflowResult:
        """Execute workflow with conditional logic."""
        for step in workflow.steps:
            try:
                # Evaluate condition if present
                if step.condition:
                    if not await self._evaluate_condition(step.condition, workflow_result.results):
                        self.logger.info(f"Skipping step {step.step_name} due to condition")
                        continue

                step_result = await self.run_step(step)
                workflow_result.results.append(step_result)

                if not step_result.success:
                    if workflow.error_strategy == ErrorStrategy.STOP:
                        workflow_result.success = False
                        workflow_result.error = f"Step {step.step_name} failed: {step_result.error}"
                        return workflow_result

                workflow_result.steps_completed += 1

            except Exception as e:
                workflow_result.success = False
                workflow_result.error = f"Exception in step {step.step_name}: {str(e)}"
                return workflow_result

        workflow_result.success = True
        return workflow_result

    async def _run_loop(self, workflow: WorkflowDefinition, workflow_result: WorkflowResult) -> WorkflowResult:
        """Execute workflow with loop logic."""
        # Simple implementation - run all steps multiple times
        iterations = workflow.metadata.get("iterations", 3)

        for iteration in range(iterations):
            self.logger.info(f"Loop iteration {iteration + 1}/{iterations}")

            for step in workflow.steps:
                try:
                    # Add iteration info to parameters
                    step_with_loop = deepcopy(step)
                    step_with_loop.parameters["iteration"] = iteration
                    step_with_loop.parameters["total_iterations"] = iterations

                    step_result = await self.run_step(step_with_loop)
                    workflow_result.results.append(step_result)

                    if not step_result.success:
                        if workflow.error_strategy == ErrorStrategy.STOP:
                            workflow_result.success = False
                            workflow_result.error = f"Step {step.step_name} failed in iteration {iteration + 1}: {step_result.error}"
                            return workflow_result

                    workflow_result.steps_completed += 1

                except Exception as e:
                    workflow_result.success = False
                    workflow_result.error = f"Exception in step {step.step_name} (iteration {iteration + 1}): {str(e)}"
                    return workflow_result

        workflow_result.success = True
        return workflow_result

    async def _run_pipeline(self, workflow: WorkflowDefinition, workflow_result: WorkflowResult) -> WorkflowResult:
        """Execute workflow as a pipeline where output of one step feeds into next."""
        pipeline_data = None

        for i, step in enumerate(workflow.steps):
            try:
                # Add pipeline data to step parameters
                if pipeline_data is not None:
                    step.parameters["pipeline_input"] = pipeline_data

                step_result = await self.run_step(step)
                workflow_result.results.append(step_result)

                if not step_result.success:
                    workflow_result.success = False
                    workflow_result.error = f"Pipeline step {step.step_name} failed: {step_result.error}"
                    return workflow_result

                # Update pipeline data with step result
                pipeline_data = step_result.result
                workflow_result.steps_completed = i + 1

            except Exception as e:
                workflow_result.success = False
                workflow_result.error = f"Exception in pipeline step {step.step_name}: {str(e)}"
                return workflow_result

        workflow_result.success = True
        workflow_result.final_result = pipeline_data
        return workflow_result

    async def run_step(self, step: WorkflowStep) -> StepResult:
        """Execute a single workflow step."""
        start_time = time.time()

        try:
            if step.step_type == "tool":
                tool = self.tool_registry.get(step.tool_name)
                if not tool:
                    raise WorkflowExecutionError(f"Tool not found: {step.tool_name}")

                result = await tool.execute(step.action, **step.parameters)
                success = True
                error = None

            elif step.step_type == "browser":
                # Use browser tool if available
                browser_tool = self.tool_registry.get("browser")
                if not browser_tool:
                    raise WorkflowExecutionError("Browser tool not available")

                result = await browser_tool.execute(step.action, **step.parameters)
                success = True
                error = None

            elif step.step_type == "delay":
                # Simple delay step
                delay_time = step.parameters.get("seconds", 1)
                await asyncio.sleep(delay_time)
                result = {"delayed": delay_time}
                success = True
                error = None

            else:
                raise WorkflowExecutionError(f"Unknown step type: {step.step_type}")

            execution_time = time.time() - start_time

            return StepResult(
                step_name=step.step_name,
                step_type=step.step_type,
                success=success,
                result=result,
                error=error,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return StepResult(
                step_name=step.step_name,
                step_type=step.step_type,
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    async def _evaluate_condition(self, condition: str, previous_results: List[StepResult]) -> bool:
        """Evaluate conditional expression based on previous results."""
        try:
            # Simple condition evaluation
            # In a production system, this would use a safer expression evaluator

            # Check for step success conditions
            if "previous_step_success" in condition:
                if previous_results and previous_results[-1].success:
                    return True
                return False

            # Check for specific result conditions
            if "contains" in condition:
                # Simple contains check
                if previous_results and previous_results[-1].result:
                    return True

            # Default to true for unknown conditions
            return True

        except Exception as e:
            self.logger.error(f"Condition evaluation failed: {e}")
            return False

    async def cleanup(self):
        """Cleanup active workflows and registered tools."""
        # Cancel active workflows
        for workflow_name in list(self.active_workflows.keys()):
            workflow_result = self.active_workflows[workflow_name]
            workflow_result.status = AutomationStatus.CANCELLED
            del self.active_workflows[workflow_name]

        # Cleanup registered tools
        for tool_name, tool in self.tool_registry.items():
            try:
                if hasattr(tool, 'cleanup'):
                    await tool.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up tool {tool_name}: {e}")


class AutomationManager:
    """Main manager for all automation tools."""

    def __init__(self):
        self.browser_tool: Optional[BrowserAutomationTool] = None
        self.workflow_orchestrator: WorkflowOrchestrator = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self, browser_engine: BrowserEngine = BrowserEngine.CHROMIUM) -> bool:
        """Initialize all automation tools."""
        try:
            # Initialize browser automation
            self.browser_tool = BrowserAutomationTool(browser_engine=browser_engine)
            browser_initialized = await self.browser_tool.initialize()

            if not browser_initialized:
                self.logger.error("Failed to initialize browser automation")
                return False

            # Initialize workflow orchestrator
            self.workflow_orchestrator = WorkflowOrchestrator()
            self.workflow_orchestrator.register_tool("browser", self.browser_tool)

            self.logger.info("Automation manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize automation manager: {e}")
            return False

    async def execute_browser_actions(self, actions: List[BrowserAction]) -> List[Dict[str, Any]]:
        """Execute a sequence of browser actions."""
        if not self.browser_tool:
            raise AutomationError("Browser tool not initialized")

        results = []
        for action in actions:
            try:
                result = await self.browser_tool.execute(
                    action.action_type,
                    selector=action.selector,
                    text=action.value,
                    options=action.options,
                    timeout=action.timeout
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "action": action.action_type
                })

        return results

    async def run_workflow(self, workflow: WorkflowDefinition) -> WorkflowResult:
        """Run a complete workflow."""
        if not self.workflow_orchestrator:
            raise AutomationError("Workflow orchestrator not initialized")

        return await self.workflow_orchestrator.run_workflow(workflow)

    def register_tool(self, name: str, tool: BaseAutomationTool):
        """Register a custom automation tool."""
        if self.workflow_orchestrator:
            self.workflow_orchestrator.register_tool(name, tool)

    async def cleanup(self):
        """Cleanup all automation resources."""
        try:
            if self.workflow_orchestrator:
                await self.workflow_orchestrator.cleanup()
            if self.browser_tool:
                await self.browser_tool.cleanup()
        except Exception as e:
            self.logger.error(f"Error during automation cleanup: {e}")


# Factory function for easy initialization
async def create_automation_manager(browser_engine: BrowserEngine = BrowserEngine.CHROMIUM) -> AutomationManager:
    """Create and initialize an automation manager instance."""
    manager = AutomationManager()
    await manager.initialize(browser_engine)
    return manager


# Export main classes and functions
__all__ = [
    'AutomationManager',
    'BrowserAutomationTool',
    'WorkflowOrchestrator',
    'BaseAutomationTool',
    'BrowserAction',
    'WorkflowStep',
    'WorkflowDefinition',
    'StepResult',
    'WorkflowResult',
    'BrowserEngine',
    'WorkflowType',
    'ErrorStrategy',
    'AutomationStatus',
    'AutomationError',
    'BrowserAutomationError',
    'WorkflowExecutionError',
    'create_automation_manager'
]