"""
Base Plugin System for TORQ Console

Defines the abstract base class and interfaces for all plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass


class PluginHook(Enum):
    """Available plugin hooks for extension points."""

    # Console lifecycle hooks
    ON_CONSOLE_START = "on_console_start"
    ON_CONSOLE_SHUTDOWN = "on_console_shutdown"

    # Command hooks
    ON_COMMAND_REGISTER = "on_command_register"
    ON_COMMAND_EXECUTE = "on_command_execute"

    # LLM hooks
    ON_LLM_RESPONSE = "on_llm_response"
    ON_LLM_REQUEST = "on_llm_request"

    # Agent hooks
    ON_AGENT_CREATE = "on_agent_create"
    ON_AGENT_EXECUTE = "on_agent_execute"

    # UI hooks
    ON_WEB_UI_START = "on_web_ui_start"
    ON_WEB_UI_ROUTE = "on_web_ui_route"

    # File operation hooks
    ON_FILE_READ = "on_file_read"
    ON_FILE_WRITE = "on_file_write"

    # Configuration hooks
    ON_CONFIG_LOAD = "on_config_load"
    ON_CONFIG_SAVE = "on_config_save"


class PluginCapability(Enum):
    """Capabilities that plugins can declare."""

    # Core capabilities
    COMMAND_EXTENSION = "command_extension"
    LLM_PROVIDER = "llm_provider"
    AGENT_TYPE = "agent_type"

    # UI capabilities
    WEB_ROUTE = "web_route"
    TERMINAL_UI = "terminal_ui"

    # Integration capabilities
    MCP_SERVER = "mcp_server"
    WEBHOOK = "webhook"

    # Data capabilities
    STORAGE = "storage"
    INDEXER = "indexer"


@dataclass
class PluginMetadata:
    """Metadata about a plugin."""

    name: str
    version: str
    description: str
    author: Optional[str] = None
    dependencies: List[str] = None
    capabilities: List[PluginCapability] = None
    hooks: List[PluginHook] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.capabilities is None:
            self.capabilities = []
        if self.hooks is None:
            self.hooks = []


class TORQPlugin(ABC):
    """
    Abstract base class for all TORQ Console plugins.

    Plugins can extend functionality by:
    - Registering new commands
    - Providing custom LLM providers
    - Adding agent types
    - Extending web UI with routes
    - Hooking into lifecycle events
    """

    def __init__(self):
        self.enabled = True
        self._hooks: Dict[PluginHook, List[Callable]] = {}

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        Initialize the plugin with TORQ Console context.

        Args:
            context: Dictionary containing console, config, and other components
        """
        pass

    def shutdown(self) -> None:
        """Called when plugin is being unloaded."""
        pass

    def register_hook(self, hook: PluginHook, callback: Callable) -> None:
        """
        Register a callback for a specific hook.

        Args:
            hook: The plugin hook to register for
            callback: Function to call when hook is triggered
        """
        if hook not in self._hooks:
            self._hooks[hook] = []
        self._hooks[hook].append(callback)

    def trigger_hook(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """
        Trigger all callbacks registered for a hook.

        Returns:
            List of results from all callbacks
        """
        results = []
        if hook in self._hooks:
            for callback in self._hooks[hook]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    # Log but don't fail other plugins
                    print(f"[Plugin] Error in {hook.value}: {e}")
        return results

    def has_capability(self, capability: PluginCapability) -> bool:
        """Check if plugin has a specific capability."""
        return capability in (self.metadata.capabilities or [])

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status information."""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "enabled": self.enabled,
            "capabilities": [c.value for c in (self.metadata.capabilities or [])],
            "hooks": [h.value for h in (self.metadata.hooks or [])]
        }
