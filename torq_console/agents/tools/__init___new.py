"""
Consolidated Tools Package for TORQ Console Agents

This package provides a unified, consolidated set of tools for TORQ Console agents.
Originally 12+ separate tool files have been consolidated into 5 focused modules
to eliminate code duplication and improve maintainability.

Consolidated Modules:
1. core_tools.py - File operations and terminal commands
2. integration_tools.py - External API and MCP server integrations
3. content_tools.py - Content generation (code, images, landing pages)
4. automation_tools.py - Browser automation and workflow orchestration
5. unified_interface.py - Common patterns and tool management

Key Improvements:
- Reduced from 12+ tool files to 5 focused modules (58% reduction)
- Eliminated duplicate code and patterns
- Created consistent interfaces across all tools
- Improved error handling and validation
- Unified configuration and credential management
- Comprehensive health monitoring and metrics
- Simplified agent integration

Usage:
    from torq_console.agents.tools import get_unified_tool_manager

    # Initialize tool manager
    manager = await get_unified_tool_manager()

    # Execute tool action
    result = await manager.execute_tool("core_tools", "file_read", file_path="example.txt")

    # Get all tools in a category
    integration_tools = manager.get_tools_by_category(ToolCategory.INTEGRATION)

    # Discover tools by capability
    code_tools = manager.discover_tools(capability="code_generation")

Author: TORQ Console Development Team
Version: 2.0.0 (Consolidated)
Date: 2024-12-14
"""

# Import unified tool manager and main classes
from .unified_interface import (
    UnifiedToolManager,
    get_unified_tool_manager,
    UnifiedTool,
    ToolMetadata,
    ToolHealthStatus,
    UnifiedResult,
    ToolCategory,
    ToolPriority,
    ToolValidationError,
    ToolRegistrationError
)

# Import consolidated tool modules for direct access
from .core_tools import (
    CoreToolsManager,
    SecureFileManager,
    SecureCommandExecutor,
    BaseCoreTool,
    ToolResult,
    ToolStatus,
    SecurityError,
    CommandNotWhitelistedError,
    DangerousCommandError,
    FileOperationsError,
    create_core_tools_manager
)

from .integration_tools import (
    IntegrationManager,
    CredentialManager,
    BaseIntegrationClient,
    HTTPIntegrationClient,
    MCPServerClient,
    TwitterIntegration,
    LinkedInIntegration,
    N8NIntegration,
    SocialMediaIntegration,
    IntegrationResult,
    IntegrationStatus,
    TransportType,
    Credential,
    IntegrationError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
    create_integration_manager
)

from .content_tools import (
    ContentManager,
    CodeGenerator,
    ImageGenerator,
    LandingPageGenerator,
    BaseContentGenerator,
    ContentRequest,
    ContentResult,
    ContentFormat,
    CodeLanguage,
    ContentQuality,
    ContentError,
    ValidationError,
    GenerationError,
    create_content_manager
)

from .automation_tools import (
    AutomationManager,
    BrowserAutomationTool,
    WorkflowOrchestrator,
    BaseAutomationTool,
    BrowserAction,
    WorkflowStep,
    WorkflowDefinition,
    StepResult,
    WorkflowResult,
    BrowserEngine,
    WorkflowType,
    ErrorStrategy,
    AutomationStatus,
    AutomationError,
    BrowserAutomationError,
    WorkflowExecutionError,
    create_automation_manager
)

# Version information
__version__ = "2.0.0"
__author__ = "TORQ Console Development Team"

# Legacy compatibility functions for smooth migration
async def create_image_generation_tool(api_key=None):
    """Legacy compatibility function for image generation tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("content_tools")

async def create_twitter_posting_tool():
    """Legacy compatibility function for Twitter tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("integration_tools")

async def create_linkedin_posting_tool():
    """Legacy compatibility function for LinkedIn tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("integration_tools")

async def create_file_operations_tool(backup_dir=None, max_backups=10):
    """Legacy compatibility function for file operations tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("core_tools")

async def create_code_generation_tool(output_dir=None):
    """Legacy compatibility function for code generation tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("content_tools")

async def create_n8n_workflow_tool():
    """Legacy compatibility function for n8n workflow tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("integration_tools")

async def create_browser_automation_tool(browser_engine="chromium", headless=True):
    """Legacy compatibility function for browser automation tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("automation_tools")

async def create_terminal_commands_tool():
    """Legacy compatibility function for terminal commands tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("core_tools")

async def create_landing_page_generator(output_dir=None):
    """Legacy compatibility function for landing page generator."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("content_tools")

async def create_mcp_client_tool():
    """Legacy compatibility function for MCP client tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("integration_tools")

async def create_multi_tool_composition_tool():
    """Legacy compatibility function for multi-tool composition tool."""
    manager = await get_unified_tool_manager()
    return manager.get_tool("automation_tools")

# Tool factory functions for new consolidated interface
async def create_tool_manager() -> UnifiedToolManager:
    """Create and initialize a unified tool manager."""
    return await get_unified_tool_manager()

async def create_core_manager() -> CoreToolsManager:
    """Create core tools manager."""
    return create_core_tools_manager()

async def create_integration_manager_instance(storage_path=None) -> IntegrationManager:
    """Create integration manager instance."""
    return create_integration_manager(storage_path)

async def create_content_manager_instance(output_dir=None) -> ContentManager:
    """Create content manager instance."""
    return create_content_manager(output_dir)

async def create_automation_manager_instance(browser_engine="chromium") -> AutomationManager:
    """Create automation manager instance."""
    from .automation_tools import BrowserEngine
    engine = BrowserEngine(browser_engine)
    return await create_automation_manager(engine)

# Utility functions
def get_available_categories() -> list:
    """Get list of available tool categories."""
    return [category.value for category in ToolCategory]

def get_category_tools(category: str, manager: UnifiedToolManager = None) -> list:
    """Get tools available in a specific category."""
    if manager is None:
        # This would need to be awaited in an async context
        raise RuntimeError("UnifiedToolManager instance required. Use get_unified_tool_manager()")

    try:
        cat_enum = ToolCategory(category)
        return manager.get_tools_by_category(cat_enum)
    except ValueError:
        return []

def discover_tools_by_capability(capability: str, manager: UnifiedToolManager = None) -> list:
    """Discover tools that have a specific capability."""
    if manager is None:
        raise RuntimeError("UnifiedToolManager instance required. Use get_unified_tool_manager()")

    return manager.discover_tools(capability=capability)

# Export all public symbols
__all__ = [
    # Main unified interface
    'UnifiedToolManager',
    'get_unified_tool_manager',
    'UnifiedTool',
    'ToolMetadata',
    'ToolHealthStatus',
    'UnifiedResult',
    'ToolCategory',
    'ToolPriority',
    'ToolValidationError',
    'ToolRegistrationError',

    # Core tools
    'CoreToolsManager',
    'SecureFileManager',
    'SecureCommandExecutor',
    'BaseCoreTool',
    'ToolResult',
    'ToolStatus',
    'SecurityError',
    'CommandNotWhitelistedError',
    'DangerousCommandError',
    'FileOperationsError',
    'create_core_tools_manager',

    # Integration tools
    'IntegrationManager',
    'CredentialManager',
    'BaseIntegrationClient',
    'HTTPIntegrationClient',
    'MCPServerClient',
    'TwitterIntegration',
    'LinkedInIntegration',
    'N8NIntegration',
    'SocialMediaIntegration',
    'IntegrationResult',
    'IntegrationStatus',
    'TransportType',
    'Credential',
    'IntegrationError',
    'AuthenticationError',
    'RateLimitError',
    'ServiceUnavailableError',
    'create_integration_manager',

    # Content tools
    'ContentManager',
    'CodeGenerator',
    'ImageGenerator',
    'LandingPageGenerator',
    'BaseContentGenerator',
    'ContentRequest',
    'ContentResult',
    'ContentFormat',
    'CodeLanguage',
    'ContentQuality',
    'ContentError',
    'ValidationError',
    'GenerationError',
    'create_content_manager',

    # Automation tools
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
    'create_automation_manager',

    # Factory functions
    'create_tool_manager',
    'create_core_manager',
    'create_integration_manager_instance',
    'create_content_manager_instance',
    'create_automation_manager_instance',

    # Utility functions
    'get_available_categories',
    'get_category_tools',
    'discover_tools_by_capability',

    # Legacy compatibility functions
    'create_image_generation_tool',
    'create_twitter_posting_tool',
    'create_linkedin_posting_tool',
    'create_file_operations_tool',
    'create_code_generation_tool',
    'create_n8n_workflow_tool',
    'create_browser_automation_tool',
    'create_terminal_commands_tool',
    'create_landing_page_generator',
    'create_mcp_client_tool',
    'create_multi_tool_composition_tool',

    # Version info
    '__version__',
    '__author__'
]