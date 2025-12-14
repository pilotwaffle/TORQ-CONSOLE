"""
Unified Tools Interface - Common Patterns and Tool Management

This module provides a consistent interface across all consolidated tools
with shared patterns, validation, and management capabilities.

Provides unified tool management:
- Base tool class with common functionality
- Tool discovery and registration system
- Unified configuration management
- Common validation and error handling patterns
- Tool health monitoring and metrics
- Centralized logging and audit trails

Author: TORQ Console Development Team
Version: 2.0.0 (Consolidated)
"""

import logging
import json
import asyncio
import inspect
from typing import Dict, List, Optional, Any, Union, Type, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod

# Import consolidated tool modules
from .core_tools import CoreToolsManager, ToolResult, ToolStatus
from .integration_tools import IntegrationManager, IntegrationResult, IntegrationStatus
from .content_tools import ContentManager, ContentResult, ContentFormat
from .automation_tools import AutomationManager, WorkflowResult, AutomationStatus

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Categories of tools for organization and discovery."""
    CORE = "core"  # File operations, terminal commands
    INTEGRATION = "integration"  # External APIs, MCP servers, social media
    CONTENT = "content"  # Code generation, image generation, landing pages
    AUTOMATION = "automation"  # Browser automation, workflow orchestration
    UTILITY = "utility"  # Helper tools and utilities


class ToolPriority(Enum):
    """Priority levels for tool execution."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ToolMetadata:
    """Metadata for tool registration and discovery."""
    name: str
    category: ToolCategory
    description: str
    version: str = "1.0.0"
    author: str = "TORQ Console Team"
    priority: ToolPriority = ToolPriority.NORMAL
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    configuration_schema: Optional[Dict[str, Any]] = None
    health_check_endpoint: Optional[str] = None


@dataclass
class ToolHealthStatus:
    """Health status of a tool."""
    tool_name: str
    status: Union[ToolStatus, IntegrationStatus, AutomationStatus]
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedResult:
    """Unified result structure across all tool types."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    tool_name: Optional[str] = None
    category: Optional[ToolCategory] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ToolValidationError(Exception):
    """Tool validation errors."""
    pass


class ToolRegistrationError(Exception):
    """Tool registration errors."""
    pass


class UnifiedTool(ABC):
    """Base class for all unified tools with common functionality."""

    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.name = metadata.name
        self.category = metadata.category
        self.logger = logging.getLogger(f"torq.tools.unified.{metadata.name}")

        # Internal state
        self._initialized = False
        self._health_status = ToolHealthStatus(
            tool_name=metadata.name,
            status=ToolStatus.UNAVAILABLE,
            last_check=datetime.now()
        )
        self._metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0
        }

    @abstractmethod
    async def initialize(self, **kwargs) -> bool:
        """Initialize the tool."""
        pass

    @abstractmethod
    async def execute(self, action: str, **kwargs) -> UnifiedResult:
        """Execute tool action."""
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup tool resources."""
        pass

    @abstractmethod
    async def health_check(self) -> ToolHealthStatus:
        """Check tool health."""
        pass

    async def _execute_with_metrics(self, action_func: Callable, action: str, **kwargs) -> UnifiedResult:
        """Execute action with metrics collection."""
        start_time = asyncio.get_event_loop().time()

        try:
            self._metrics['total_calls'] += 1

            # Execute the action
            result = await action_func(action, **kwargs)

            # Update metrics
            execution_time = asyncio.get_event_loop().time() - start_time
            self._metrics['total_execution_time'] += execution_time
            self._metrics['average_execution_time'] = (
                self._metrics['total_execution_time'] / self._metrics['total_calls']
            )

            if result.success:
                self._metrics['successful_calls'] += 1
            else:
                self._metrics['failed_calls'] += 1

            # Add execution time to result
            result.execution_time = execution_time

            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self._metrics['total_execution_time'] += execution_time
            self._metrics['failed_calls'] += 1

            self.logger.error(f"Tool {self.name} execution failed: {e}")

            return UnifiedResult(
                success=False,
                error=str(e),
                tool_name=self.name,
                category=self.category,
                execution_time=execution_time
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get tool metrics."""
        success_rate = 0.0
        if self._metrics['total_calls'] > 0:
            success_rate = (self._metrics['successful_calls'] / self._metrics['total_calls']) * 100

        return {
            **self._metrics,
            'success_rate_percent': success_rate,
            'health_status': self._health_status.status.value if self._health_status else 'unknown'
        }

    def get_info(self) -> Dict[str, Any]:
        """Get tool information."""
        return {
            'metadata': asdict(self.metadata),
            'initialized': self._initialized,
            'metrics': self.get_metrics(),
            'health_status': {
                'status': self._health_status.status.value,
                'last_check': self._health_status.last_check.isoformat(),
                'response_time': self._health_status.response_time,
                'error_message': self._health_status.error_message
            }
        }


class CoreToolWrapper(UnifiedTool):
    """Wrapper for core tools manager."""

    def __init__(self):
        metadata = ToolMetadata(
            name="core_tools",
            category=ToolCategory.CORE,
            description="File operations and terminal command execution",
            capabilities=["file_operations", "terminal_commands", "security_controls"],
            tags=["files", "terminal", "security"]
        )
        super().__init__(metadata)
        self.core_manager: Optional[CoreToolsManager] = None

    async def initialize(self, **kwargs) -> bool:
        """Initialize core tools manager."""
        try:
            self.core_manager = CoreToolsManager()
            health_result = await self.core_manager.check_health()

            self._initialized = health_result.success
            if self._initialized:
                self.logger.info("Core tools initialized successfully")
            else:
                self.logger.error(f"Core tools initialization failed: {health_result.error}")

            return self._initialized

        except Exception as e:
            self.logger.error(f"Core tools initialization exception: {e}")
            return False

    async def execute(self, action: str, **kwargs) -> UnifiedResult:
        """Execute core tool action."""
        if not self._initialized or not self.core_manager:
            return UnifiedResult(
                success=False,
                error="Core tools not initialized",
                tool_name=self.name,
                category=self.category
            )

        async def action_func(action: str, **kwargs) -> UnifiedResult:
            if action.startswith('file_'):
                result = await self.core_manager.execute_file_operation(
                    action.replace('file_', ''), **kwargs
                )
            elif action == 'command':
                result = await self.core_manager.execute_command(**kwargs)
            else:
                return UnifiedResult(
                    success=False,
                    error=f"Unknown core action: {action}",
                    tool_name=self.name,
                    category=self.category
                )

            return UnifiedResult(
                success=result.success,
                data=result.data,
                error=result.error,
                tool_name=self.name,
                category=self.category,
                metadata=result.metadata
            )

        return await self._execute_with_metrics(action_func, action, **kwargs)

    async def cleanup(self):
        """Cleanup core tools manager."""
        if self.core_manager:
            # Core tools manager doesn't have explicit cleanup
            self.core_manager = None
        self._initialized = False

    async def health_check(self) -> ToolHealthStatus:
        """Check core tools health."""
        start_time = asyncio.get_event_loop().time()

        if not self.core_manager:
            return ToolHealthStatus(
                tool_name=self.name,
                status=ToolStatus.UNAVAILABLE,
                last_check=datetime.now(),
                error_message="Core tools manager not initialized"
            )

        try:
            health_result = await self.core_manager.check_health()
            response_time = asyncio.get_event_loop().time() - start_time

            status = ToolStatus.AVAILABLE if health_result.success else ToolStatus.ERROR

            self._health_status = ToolHealthStatus(
                tool_name=self.name,
                status=status,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=health_result.error if not health_result.success else None,
                metadata=health_result.data
            )

        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            self._health_status = ToolHealthStatus(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=str(e)
            )

        return self._health_status


class IntegrationToolWrapper(UnifiedTool):
    """Wrapper for integration tools manager."""

    def __init__(self):
        metadata = ToolMetadata(
            name="integration_tools",
            category=ToolCategory.INTEGRATION,
            description="External API and MCP server integrations",
            capabilities=["http_api", "mcp_servers", "social_media", "n8n_workflows"],
            tags=["api", "mcp", "twitter", "linkedin", "n8n"],
            dependencies=["httpx"]
        )
        super().__init__(metadata)
        self.integration_manager: Optional[IntegrationManager] = None

    async def initialize(self, **kwargs) -> bool:
        """Initialize integration tools manager."""
        try:
            storage_path = kwargs.get('storage_path')
            self.integration_manager = IntegrationManager(storage_path)

            # Initialize integrations
            init_result = await self.integration_manager.initialize()
            self._initialized = init_result.success

            if self._initialized:
                self.logger.info("Integration tools initialized successfully")
            else:
                self.logger.error(f"Integration tools initialization failed: {init_result.error}")

            return self._initialized

        except Exception as e:
            self.logger.error(f"Integration tools initialization exception: {e}")
            return False

    async def execute(self, action: str, **kwargs) -> UnifiedResult:
        """Execute integration tool action."""
        if not self._initialized or not self.integration_manager:
            return UnifiedResult(
                success=False,
                error="Integration tools not initialized",
                tool_name=self.name,
                category=self.category
            )

        async def action_func(action: str, **kwargs) -> UnifiedResult:
            if action == "check_connections":
                result_data = await self.integration_manager.check_all_connections()
                return UnifiedResult(
                    success=True,
                    data=result_data,
                    tool_name=self.name,
                    category=self.category
                )
            elif action == "add_mcp_server":
                result = await self.integration_manager.add_mcp_server(
                    kwargs.get('service_name'),
                    kwargs.get('server_config', {})
                )
                return UnifiedResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    tool_name=self.name,
                    category=self.category
                )
            elif action == "add_n8n_integration":
                result = await self.integration_manager.add_n8n_integration(
                    kwargs.get('base_url', 'http://localhost:5678')
                )
                return UnifiedResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    tool_name=self.name,
                    category=self.category
                )
            else:
                # Try to execute on specific client
                service_name = kwargs.get('service_name')
                if service_name:
                    client = self.integration_manager.get_client(service_name)
                    if client and hasattr(client, action):
                        if asyncio.iscoroutinefunction(getattr(client, action)):
                            result = await getattr(client, action)(**kwargs)
                        else:
                            result = getattr(client, action)(**kwargs)

                        return UnifiedResult(
                            success=result.success,
                            data=result.data,
                            error=result.error,
                            tool_name=self.name,
                            category=self.category
                        )

                return UnifiedResult(
                    success=False,
                    error=f"Unknown integration action: {action}",
                    tool_name=self.name,
                    category=self.category
                )

        return await self._execute_with_metrics(action_func, action, **kwargs)

    async def cleanup(self):
        """Cleanup integration tools manager."""
        if self.integration_manager:
            # Integration manager cleanup would go here
            self.integration_manager = None
        self._initialized = False

    async def health_check(self) -> ToolHealthStatus:
        """Check integration tools health."""
        start_time = asyncio.get_event_loop().time()

        if not self.integration_manager:
            return ToolHealthStatus(
                tool_name=self.name,
                status=IntegrationStatus.DISCONNECTED,
                last_check=datetime.now(),
                error_message="Integration tools manager not initialized"
            )

        try:
            connection_statuses = await self.integration_manager.check_all_connections()
            response_time = asyncio.get_event_loop().time() - start_time

            # Determine overall status
            all_connected = all(status.success for status in connection_statuses.values())
            status = IntegrationStatus.CONNECTED if all_connected else IntegrationStatus.ERROR

            error_messages = []
            for service, status_result in connection_statuses.items():
                if not status_result.success:
                    error_messages.append(f"{service}: {status_result.error}")

            self._health_status = ToolHealthStatus(
                tool_name=self.name,
                status=status,
                last_check=datetime.now(),
                response_time=response_time,
                error_message="; ".join(error_messages) if error_messages else None,
                metadata={'connection_statuses': connection_statuses}
            )

        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            self._health_status = ToolHealthStatus(
                tool_name=self.name,
                status=IntegrationStatus.ERROR,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=str(e)
            )

        return self._health_status


class ContentToolWrapper(UnifiedTool):
    """Wrapper for content tools manager."""

    def __init__(self):
        metadata = ToolMetadata(
            name="content_tools",
            category=ToolCategory.CONTENT,
            description="Content generation and creative capabilities",
            capabilities=["code_generation", "image_generation", "landing_pages"],
            tags=["content", "code", "images", "html"],
            dependencies=["image_generation"]
        )
        super().__init__(metadata)
        self.content_manager: Optional[ContentManager] = None

    async def initialize(self, **kwargs) -> bool:
        """Initialize content tools manager."""
        try:
            output_dir = kwargs.get('output_dir')
            self.content_manager = ContentManager(output_dir)
            self._initialized = True
            self.logger.info("Content tools initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Content tools initialization exception: {e}")
            return False

    async def execute(self, action: str, **kwargs) -> UnifiedResult:
        """Execute content tool action."""
        if not self._initialized or not self.content_manager:
            return UnifiedResult(
                success=False,
                error="Content tools not initialized",
                tool_name=self.name,
                category=self.category
            )

        async def action_func(action: str, **kwargs) -> UnifiedResult:
            if action == "generate_content":
                from .content_tools import ContentRequest, ContentFormat
                content_request = ContentRequest(**kwargs)
                result = await self.content_manager.generate_content(content_request)
                return UnifiedResult(
                    success=result.success,
                    data=result.content,
                    error=result.error,
                    tool_name=self.name,
                    category=self.category,
                    metadata={
                        'format': result.format.value,
                        'quality': result.quality.value,
                        'file_path': result.file_path
                    }
                )
            elif action == "validate_content":
                from .content_tools import ContentFormat
                content_format = ContentFormat(kwargs.get('format', 'text'))
                result = await self.content_manager.validate_content(
                    kwargs.get('content'), content_format
                )
                return UnifiedResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    tool_name=self.name,
                    category=self.category,
                    metadata={'quality': result.quality.value if result.quality else None}
                )
            elif action == "lint_code":
                from .content_tools import CodeLanguage
                language = CodeLanguage(kwargs.get('language', 'python'))
                result = await self.content_manager.lint_code(
                    kwargs.get('code'), language
                )
                return UnifiedResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    tool_name=self.name,
                    category=self.category
                )
            else:
                return UnifiedResult(
                    success=False,
                    error=f"Unknown content action: {action}",
                    tool_name=self.name,
                    category=self.category
                )

        return await self._execute_with_metrics(action_func, action, **kwargs)

    async def cleanup(self):
        """Cleanup content tools manager."""
        if self.content_manager:
            # Content manager cleanup would go here
            self.content_manager = None
        self._initialized = False

    async def health_check(self) -> ToolHealthStatus:
        """Check content tools health."""
        start_time = asyncio.get_event_loop().time()

        if not self.content_manager:
            return ToolHealthStatus(
                tool_name=self.name,
                status=ToolStatus.UNAVAILABLE,
                last_check=datetime.now(),
                error_message="Content tools manager not initialized"
            )

        try:
            # Simple health check - try to validate some content
            test_content = "Hello, World!"
            result = await self.content_manager.validate_content(test_content, ContentFormat.TEXT)
            response_time = asyncio.get_event_loop().time() - start_time

            status = ToolStatus.AVAILABLE if result.success else ToolStatus.ERROR

            self._health_status = ToolHealthStatus(
                tool_name=self.name,
                status=status,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=result.error if not result.success else None
            )

        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            self._health_status = ToolHealthStatus(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=str(e)
            )

        return self._health_status


class AutomationToolWrapper(UnifiedTool):
    """Wrapper for automation tools manager."""

    def __init__(self):
        metadata = ToolMetadata(
            name="automation_tools",
            category=ToolCategory.AUTOMATION,
            description="Browser automation and workflow orchestration",
            capabilities=["browser_automation", "workflow_orchestration", "web_scraping"],
            tags=["automation", "browser", "workflows", "scraping"],
            dependencies=["playwright"]
        )
        super().__init__(metadata)
        self.automation_manager: Optional[AutomationManager] = None

    async def initialize(self, **kwargs) -> bool:
        """Initialize automation tools manager."""
        try:
            self.automation_manager = AutomationManager()
            browser_engine = kwargs.get('browser_engine', 'chromium')

            from .automation_tools import BrowserEngine
            engine = BrowserEngine(browser_engine)

            self._initialized = await self.automation_manager.initialize(engine)

            if self._initialized:
                self.logger.info("Automation tools initialized successfully")
            else:
                self.logger.error("Automation tools initialization failed")

            return self._initialized

        except Exception as e:
            self.logger.error(f"Automation tools initialization exception: {e}")
            return False

    async def execute(self, action: str, **kwargs) -> UnifiedResult:
        """Execute automation tool action."""
        if not self._initialized or not self.automation_manager:
            return UnifiedResult(
                success=False,
                error="Automation tools not initialized",
                tool_name=self.name,
                category=self.category
            )

        async def action_func(action: str, **kwargs) -> UnifiedResult:
            if action == "browser_actions":
                from .automation_tools import BrowserAction
                actions = [BrowserAction(**action_data) for action_data in kwargs.get('actions', [])]
                results = await self.automation_manager.execute_browser_actions(actions)
                return UnifiedResult(
                    success=True,
                    data=results,
                    tool_name=self.name,
                    category=self.category
                )
            elif action == "run_workflow":
                from .automation_tools import WorkflowDefinition, WorkflowType
                workflow_data = kwargs.get('workflow')
                workflow_type = WorkflowType(workflow_data.get('workflow_type', 'sequential'))
                workflow = WorkflowDefinition(
                    name=workflow_data.get('name', 'unnamed_workflow'),
                    description=workflow_data.get('description', ''),
                    workflow_type=workflow_type,
                    steps=[]  # Steps would need to be properly constructed
                )
                result = await self.automation_manager.run_workflow(workflow)
                return UnifiedResult(
                    success=result.success,
                    data=result,
                    error=result.error,
                    tool_name=self.name,
                    category=self.category,
                    metadata={
                        'steps_completed': result.steps_completed,
                        'total_steps': result.total_steps,
                        'execution_time': result.execution_time
                    }
                )
            else:
                return UnifiedResult(
                    success=False,
                    error=f"Unknown automation action: {action}",
                    tool_name=self.name,
                    category=self.category
                )

        return await self._execute_with_metrics(action_func, action, **kwargs)

    async def cleanup(self):
        """Cleanup automation tools manager."""
        if self.automation_manager:
            await self.automation_manager.cleanup()
            self.automation_manager = None
        self._initialized = False

    async def health_check(self) -> ToolHealthStatus:
        """Check automation tools health."""
        start_time = asyncio.get_event_loop().time()

        if not self.automation_manager:
            return ToolHealthStatus(
                tool_name=self.name,
                status=AutomationStatus.FAILED,
                last_check=datetime.now(),
                error_message="Automation tools manager not initialized"
            )

        try:
            # Simple health check - check if browser tool is available
            if self.automation_manager.browser_tool:
                status = AutomationStatus.COMPLETED
                error_message = None
            else:
                status = AutomationStatus.FAILED
                error_message = "Browser tool not available"

            response_time = asyncio.get_event_loop().time() - start_time

            self._health_status = ToolHealthStatus(
                tool_name=self.name,
                status=status,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=error_message
            )

        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            self._health_status = ToolHealthStatus(
                tool_name=self.name,
                status=AutomationStatus.FAILED,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=str(e)
            )

        return self._health_status


class UnifiedToolManager:
    """Main manager for all unified tools with discovery and orchestration."""

    def __init__(self):
        self.tools: Dict[str, UnifiedTool] = {}
        self.tools_by_category: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        self.logger = logging.getLogger(__name__)

    async def initialize(self, **kwargs) -> bool:
        """Initialize all unified tools."""
        try:
            # Register and initialize all tool wrappers
            tool_wrappers = [
                CoreToolWrapper(),
                IntegrationToolWrapper(),
                ContentToolWrapper(),
                AutomationToolWrapper()
            ]

            for tool in tool_wrappers:
                await self.register_tool(tool, **kwargs)

            self.logger.info(f"Unified tool manager initialized with {len(self.tools)} tools")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize unified tool manager: {e}")
            return False

    async def register_tool(self, tool: UnifiedTool, **kwargs) -> bool:
        """Register and initialize a tool."""
        try:
            # Initialize the tool
            initialized = await tool.initialize(**kwargs)
            if not initialized:
                self.logger.error(f"Failed to initialize tool: {tool.name}")
                return False

            # Register the tool
            self.tools[tool.name] = tool
            self.tools_by_category[tool.category].append(tool.name)

            self.logger.info(f"Registered tool: {tool.name} in category {tool.category.value}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register tool {tool.name}: {e}")
            return False

    def get_tool(self, name: str) -> Optional[UnifiedTool]:
        """Get tool by name."""
        return self.tools.get(name)

    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get all tools in a category."""
        return self.tools_by_category.get(category, []).copy()

    def discover_tools(self, tag: Optional[str] = None, capability: Optional[str] = None) -> List[str]:
        """Discover tools based on tags or capabilities."""
        matching_tools = []

        for tool in self.tools.values():
            # Check tag filter
            if tag and tag not in tool.metadata.tags:
                continue

            # Check capability filter
            if capability and capability not in tool.metadata.capabilities:
                continue

            matching_tools.append(tool.name)

        return matching_tools

    async def execute_tool(self, tool_name: str, action: str, **kwargs) -> UnifiedResult:
        """Execute action on a specific tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            return UnifiedResult(
                success=False,
                error=f"Tool not found: {tool_name}",
                tool_name=tool_name
            )

        return await tool.execute(action, **kwargs)

    async def health_check_all(self) -> Dict[str, ToolHealthStatus]:
        """Perform health check on all tools."""
        health_statuses = {}

        for tool_name, tool in self.tools.items():
            try:
                health_status = await tool.health_check()
                health_statuses[tool_name] = health_status
            except Exception as e:
                self.logger.error(f"Health check failed for {tool_name}: {e}")
                health_statuses[tool_name] = ToolHealthStatus(
                    tool_name=tool_name,
                    status=ToolStatus.ERROR,
                    last_check=datetime.now(),
                    error_message=str(e)
                )

        return health_statuses

    async def cleanup_all(self):
        """Cleanup all tools."""
        for tool_name, tool in self.tools.items():
            try:
                await tool.cleanup()
                self.logger.info(f"Cleaned up tool: {tool_name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up tool {tool_name}: {e}")

        self.tools.clear()
        for category in self.tools_by_category:
            self.tools_by_category[category].clear()

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        total_tools = len(self.tools)
        tools_by_category_count = {
            category.value: len(tools) for category, tools in self.tools_by_category.items()
        }

        return {
            'total_tools': total_tools,
            'tools_by_category': tools_by_category_count,
            'tool_names': list(self.tools.keys()),
            'available_categories': [category.value for category, tools in self.tools_by_category.items() if tools]
        }


# Global instance for easy access
_unified_manager: Optional[UnifiedToolManager] = None


async def get_unified_tool_manager() -> UnifiedToolManager:
    """Get or create the global unified tool manager."""
    global _unified_manager
    if _unified_manager is None:
        _unified_manager = UnifiedToolManager()
        await _unified_manager.initialize()
    return _unified_manager


# Export main classes and functions
__all__ = [
    'UnifiedToolManager',
    'UnifiedTool',
    'CoreToolWrapper',
    'IntegrationToolWrapper',
    'ContentToolWrapper',
    'AutomationToolWrapper',
    'ToolMetadata',
    'ToolHealthStatus',
    'UnifiedResult',
    'ToolCategory',
    'ToolPriority',
    'ToolValidationError',
    'ToolRegistrationError',
    'get_unified_tool_manager'
]