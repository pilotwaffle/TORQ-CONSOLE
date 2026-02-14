"""
Plugin Registry for TORQ Console

Central registry managing all loaded plugins and their capabilities.
"""

import logging
from typing import Dict, List, Optional, Any, Callable

from .base import TORQPlugin, PluginMetadata, PluginHook, PluginCapability


class PluginRegistry:
    """
    Central registry for all plugins.

    Manages plugin lifecycle, capability queries, and hook triggering.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._plugins: Dict[str, TORQPlugin] = {}
        self._capabilities: Dict[PluginCapability, List[str]] = {}
        self._hooks: Dict[PluginHook, List[Callable]] = {}

    def register(self, plugin: TORQPlugin) -> bool:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Returns:
            True if registered successfully
        """
        metadata = plugin.metadata

        # Check for duplicate
        if metadata.name in self._plugins:
            self.logger.warning(f"Plugin {metadata.name} already registered")
            return False

        # Check dependencies
        for dep in metadata.dependencies or []:
            if dep not in self._plugins:
                self.logger.error(f"Plugin {metadata.name} requires {dep} which is not available")
                return False

        # Register plugin
        self._plugins[metadata.name] = plugin

        # Register capabilities
        for capability in metadata.capabilities or []:
            if capability not in self._capabilities:
                self._capabilities[capability] = []
            self._capabilities[capability].append(metadata.name)

        # Register hooks
        for hook in metadata.hooks or []:
            if hook not in self._hooks:
                self._hooks[hook] = []
            # Get plugin's hook callbacks if available
            if hasattr(plugin, "get_hook_callbacks"):
                callbacks = plugin.get_hook_callbacks(hook)
                for callback in callbacks or []:
                    self._hooks[hook].append(callback)

        self.logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")
        return True

    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin by name.

        Args:
            name: Plugin name

        Returns:
            True if unregistered successfully
        """
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]

        # Remove capabilities
        for capability in list(self._capabilities.keys()):
            if name in self._capabilities[capability]:
                self._capabilities[capability].remove(name)

        # Remove hooks
        for hook in list(self._hooks.keys()):
            # Plugin-specific hooks would need to be tracked per-plugin
            pass

        del self._plugins[name]
        self.logger.info(f"Unregistered plugin: {name}")
        return True

    def get_plugin(self, name: str) -> Optional[TORQPlugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, TORQPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    def get_plugins_with_capability(self, capability: PluginCapability) -> List[TORQPlugin]:
        """
        Get all plugins that have a specific capability.

        Args:
            capability: Capability to filter by

        Returns:
            List of plugins with the capability
        """
        plugin_names = self._capabilities.get(capability, [])
        return [self._plugins[name] for name in plugin_names if name in self._plugins]

    def trigger_hook(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """
        Trigger all callbacks registered for a hook.

        Args:
            hook: Hook to trigger
            *args, **kwargs: Arguments to pass to callbacks

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
                    self.logger.error(f"Error in hook {hook.value}: {e}")

        return results

    def register_hook_callback(self, plugin_name: str, hook: PluginHook, callback: Callable) -> bool:
        """
        Register a hook callback for a specific plugin.

        Args:
            plugin_name: Name of plugin registering the callback
            hook: Hook to register for
            callback: Function to call when hook is triggered

        Returns:
            True if registered successfully
        """
        if plugin_name not in self._plugins:
            return False

        if hook not in self._hooks:
            self._hooks[hook] = []

        self._hooks[hook].append(callback)
        return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get registry status.

        Returns:
            Dictionary with plugin statistics and capability mappings
        """
        return {
            "plugin_count": len(self._plugins),
            "plugins": {name: plugin.get_status() for name, plugin in self._plugins.items()},
            "capabilities": {cap.value: names for cap, names in self._capabilities.items()},
            "hooks": {hook.value: len(callbacks) for hook, callbacks in self._hooks.items()}
        }


# Global registry instance
_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
