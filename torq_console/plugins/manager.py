"""
Plugin Manager for TORQ Console

High-level interface for managing plugins throughout the application lifecycle.
"""

import logging
from typing import Dict, List, Optional, Any

from .loader import PluginLoader
from .registry import PluginRegistry, get_registry
from .base import TORQPlugin, PluginMetadata, PluginHook, PluginCapability


class PluginManager:
    """
    High-level manager for TORQ Console plugin system.

    Provides unified interface for:
    - Loading and unloading plugins
    - Querying plugins by capability
    - Triggering plugin hooks
    - Managing plugin lifecycle
    """

    def __init__(self, plugin_paths: Optional[List[str]] = None):
        """
        Initialize plugin manager.

        Args:
            plugin_paths: Additional paths to search for plugins
        """
        self.logger = logging.getLogger(__name__)
        self.registry = get_registry()
        self.loader = PluginLoader(plugin_paths)
        self.context: Dict[str, Any] = {}

    def initialize(self, context: Dict[str, Any]) -> None:
        """
        Initialize the plugin system with TORQ Console context.

        Args:
            context: Dictionary containing console, config, and components
        """
        self.context = context

        # Load all plugins
        plugins = self.loader.load_all()

        # Register all loaded plugins
        for plugin in plugins.values():
            self.registry.register(plugin)

        # Initialize all plugins
        for plugin in plugins.values():
            try:
                plugin.initialize(context)
                self.logger.info(f"Initialized plugin: {plugin.metadata.name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize plugin {plugin.metadata.name}: {e}")

        # Trigger startup hooks
        self.trigger_hook(PluginHook.ON_CONSOLE_START, context)

    def shutdown(self) -> None:
        """Shutdown the plugin system gracefully."""
        # Trigger shutdown hooks
        self.trigger_hook(PluginHook.ON_CONSOLE_SHUTDOWN, self.context)

        # Shutdown all plugins
        for plugin in self.registry.get_all_plugins().values():
            try:
                plugin.shutdown()
                self.logger.info(f"Shutdown plugin: {plugin.metadata.name}")
            except Exception as e:
                self.logger.error(f"Error shutting down plugin {plugin.metadata.name}: {e}")

    def trigger_hook(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """
        Trigger a hook across all plugins.

        Args:
            hook: Hook to trigger
            *args, **kwargs: Arguments to pass to callbacks

        Returns:
            List of results from all callbacks
        """
        return self.registry.trigger_hook(hook, *args, **kwargs)

    def get_plugins_with_capability(self, capability: PluginCapability) -> List[TORQPlugin]:
        """
        Get all plugins with a specific capability.

        Args:
            capability: Capability to filter by

        Returns:
            List of plugins with the capability
        """
        return self.registry.get_plugins_with_capability(capability)

    def get_plugin(self, name: str) -> Optional[TORQPlugin]:
        """
        Get a specific plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self.registry.get_plugin(name)

    def load_plugin(self, plugin_path: str) -> bool:
        """
        Load a plugin from a specific path.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            True if loaded successfully
        """
        from pathlib import Path

        plugin_dir = Path(plugin_path)
        plugin = self.loader.load_from_directory(plugin_dir)

        if plugin:
            self.registry.register(plugin)
            try:
                plugin.initialize(self.context)
                self.logger.info(f"Loaded and initialized plugin: {plugin.metadata.name}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to initialize plugin {plugin.metadata.name}: {e}")
                return False
        return False

    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin by name.

        Args:
            name: Plugin name

        Returns:
            True if unloaded successfully
        """
        return self.registry.unregister(name)

    def get_status(self) -> Dict[str, Any]:
        """
        Get plugin system status.

        Returns:
            Dictionary with system status information
        """
        return {
            "registry": self.registry.get_status(),
            "loader": {
                "search_paths": self.loader.plugin_paths,
                "loaded_count": len(self.loader.loaded_plugins)
            }
        }
