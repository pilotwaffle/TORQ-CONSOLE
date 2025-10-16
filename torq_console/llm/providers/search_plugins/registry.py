"""
Plugin Registry

Manages registration, discovery, and lifecycle of search plugins.
"""

from typing import Dict, List, Optional, Type
import logging
from .base import SearchPlugin, PluginMetadata, PluginNotFoundError


class PluginRegistry:
    """
    Central registry for managing search plugins.

    Features:
    - Plugin registration and discovery
    - Plugin lifecycle management (init, cleanup)
    - Plugin querying and filtering
    - Dependency resolution
    """

    def __init__(self):
        """Initialize the plugin registry."""
        self.logger = logging.getLogger(__name__)

        # Registered plugins: {plugin_name: plugin_instance}
        self._plugins: Dict[str, SearchPlugin] = {}

        # Plugin classes: {plugin_name: plugin_class}
        self._plugin_classes: Dict[str, Type[SearchPlugin]] = {}

        # Initialization status: {plugin_name: bool}
        self._initialization_status: Dict[str, bool] = {}

        self.logger.info("[PLUGIN_REGISTRY] Plugin registry initialized")

    def register(
        self,
        plugin_class: Type[SearchPlugin],
        auto_initialize: bool = True
    ) -> bool:
        """
        Register a plugin class.

        Args:
            plugin_class: Plugin class (not instance)
            auto_initialize: Automatically initialize the plugin

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Create instance to get metadata
            temp_instance = plugin_class()
            metadata = temp_instance.get_metadata()

            if not metadata:
                self.logger.error(f"[PLUGIN_REGISTRY] Plugin {plugin_class.__name__} has no metadata")
                return False

            plugin_name = metadata.name

            # Check if already registered
            if plugin_name in self._plugin_classes:
                self.logger.warning(f"[PLUGIN_REGISTRY] Plugin '{plugin_name}' already registered")
                return False

            # Register the class
            self._plugin_classes[plugin_name] = plugin_class
            self.logger.info(f"[PLUGIN_REGISTRY] Registered plugin: {plugin_name} v{metadata.version}")

            # Auto-initialize if requested
            if auto_initialize:
                return self._initialize_plugin(plugin_name)

            return True

        except Exception as e:
            self.logger.error(f"[PLUGIN_REGISTRY] Error registering plugin: {e}")
            return False

    def _initialize_plugin(self, plugin_name: str) -> bool:
        """
        Initialize a registered plugin.

        Args:
            plugin_name: Name of the plugin to initialize

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if plugin_name not in self._plugin_classes:
                raise PluginNotFoundError(f"Plugin '{plugin_name}' not registered")

            # Create instance
            plugin_class = self._plugin_classes[plugin_name]
            plugin_instance = plugin_class()

            # Initialize
            import asyncio
            if asyncio.iscoroutinefunction(plugin_instance.initialize):
                # Check if event loop is running
                try:
                    loop = asyncio.get_running_loop()
                    # Event loop is running - skip async init for now
                    # The plugin will be initialized when first used
                    success = True
                    self.logger.warning(f"[PLUGIN_REGISTRY] Skipping async init for '{plugin_name}' (event loop already running)")
                except RuntimeError:
                    # No event loop running - safe to use run_until_complete
                    loop = asyncio.get_event_loop()
                    success = loop.run_until_complete(plugin_instance.initialize())
            else:
                success = plugin_instance.initialize()

            if success:
                self._plugins[plugin_name] = plugin_instance
                self._initialization_status[plugin_name] = True
                self.logger.info(f"[PLUGIN_REGISTRY] Initialized plugin: {plugin_name}")
            else:
                self._initialization_status[plugin_name] = False
                self.logger.error(f"[PLUGIN_REGISTRY] Failed to initialize plugin: {plugin_name}")

            return success

        except Exception as e:
            self.logger.error(f"[PLUGIN_REGISTRY] Error initializing plugin '{plugin_name}': {e}")
            self._initialization_status[plugin_name] = False
            return False

    def unregister(self, plugin_name: str) -> bool:
        """
        Unregister and cleanup a plugin.

        Args:
            plugin_name: Name of the plugin to unregister

        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            # Cleanup if initialized
            if plugin_name in self._plugins:
                plugin = self._plugins[plugin_name]
                import asyncio
                if asyncio.iscoroutinefunction(plugin.cleanup):
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(plugin.cleanup())
                else:
                    plugin.cleanup()

                del self._plugins[plugin_name]

            # Remove from registry
            if plugin_name in self._plugin_classes:
                del self._plugin_classes[plugin_name]

            if plugin_name in self._initialization_status:
                del self._initialization_status[plugin_name]

            self.logger.info(f"[PLUGIN_REGISTRY] Unregistered plugin: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"[PLUGIN_REGISTRY] Error unregistering plugin '{plugin_name}': {e}")
            return False

    def get_plugin(self, plugin_name: str) -> Optional[SearchPlugin]:
        """
        Get an initialized plugin instance.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin instance or None if not found/initialized
        """
        return self._plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, SearchPlugin]:
        """
        Get all initialized plugins.

        Returns:
            Dictionary of {plugin_name: plugin_instance}
        """
        return self._plugins.copy()

    def list_plugins(self, include_uninitialized: bool = False) -> List[str]:
        """
        List all plugin names.

        Args:
            include_uninitialized: Include plugins that are registered but not initialized

        Returns:
            List of plugin names
        """
        if include_uninitialized:
            return list(self._plugin_classes.keys())
        else:
            return list(self._plugins.keys())

    def get_plugins_by_capability(
        self,
        search_type: str
    ) -> List[SearchPlugin]:
        """
        Get all plugins that support a specific search type.

        Args:
            search_type: Type of search (general, news, academic)

        Returns:
            List of plugin instances that support the search type
        """
        matching_plugins = []

        for plugin in self._plugins.values():
            if plugin.supports_search_type(search_type):
                matching_plugins.append(plugin)

        return matching_plugins

    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """
        Get metadata for a specific plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            PluginMetadata object or None if not found
        """
        plugin = self._plugins.get(plugin_name)
        if plugin:
            return plugin.get_metadata()
        return None

    def get_all_metadata(self) -> Dict[str, PluginMetadata]:
        """
        Get metadata for all plugins.

        Returns:
            Dictionary of {plugin_name: metadata}
        """
        metadata_dict = {}

        for plugin_name, plugin in self._plugins.items():
            metadata = plugin.get_metadata()
            if metadata:
                metadata_dict[plugin_name] = metadata

        return metadata_dict

    def is_plugin_available(self, plugin_name: str) -> bool:
        """
        Check if a plugin is available and ready to use.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if available, False otherwise
        """
        plugin = self._plugins.get(plugin_name)
        return plugin.is_available() if plugin else False

    async def health_check_all(self) -> Dict[str, Dict]:
        """
        Run health checks on all plugins.

        Returns:
            Dictionary of {plugin_name: health_check_result}
        """
        health_results = {}

        for plugin_name, plugin in self._plugins.items():
            try:
                health = await plugin.health_check()
                health_results[plugin_name] = health
            except Exception as e:
                health_results[plugin_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return health_results

    def get_statistics(self) -> Dict:
        """
        Get registry statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'total_registered': len(self._plugin_classes),
            'total_initialized': len(self._plugins),
            'total_failed': sum(
                1 for status in self._initialization_status.values()
                if not status
            ),
            'available_plugins': len([
                p for p in self._plugins.values() if p.is_available()
            ])
        }


# Global singleton instance
_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """
    Get the global plugin registry instance.

    Returns:
        PluginRegistry singleton
    """
    return _registry
