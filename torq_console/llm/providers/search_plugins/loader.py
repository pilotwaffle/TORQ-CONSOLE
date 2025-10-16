"""
Plugin Loader

Discovers and dynamically loads search plugins from the filesystem.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import List, Type, Optional
import logging
from .base import SearchPlugin, PluginLoadError
from .registry import PluginRegistry, get_registry


class PluginLoader:
    """
    Dynamic plugin loader.

    Features:
    - Discover plugins from directories
    - Load plugins from Python modules
    - Validate plugin structure
    - Handle loading errors gracefully
    """

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """
        Initialize the plugin loader.

        Args:
            registry: PluginRegistry to register loaded plugins (default: global registry)
        """
        self.logger = logging.getLogger(__name__)
        self.registry = registry or get_registry()

        # Track loaded plugins
        self.loaded_plugins: List[str] = []

    def discover_plugins(self, plugin_dir: str) -> List[str]:
        """
        Discover plugin files in a directory.

        Args:
            plugin_dir: Directory to search for plugins

        Returns:
            List of plugin file paths
        """
        plugin_dir_path = Path(plugin_dir)

        if not plugin_dir_path.exists():
            self.logger.warning(f"[PLUGIN_LOADER] Plugin directory not found: {plugin_dir}")
            return []

        plugin_files = []

        # Find all .py files that don't start with '_'
        for file_path in plugin_dir_path.glob("*.py"):
            if not file_path.name.startswith('_'):
                plugin_files.append(str(file_path))

        self.logger.info(f"[PLUGIN_LOADER] Discovered {len(plugin_files)} plugin files in {plugin_dir}")
        return plugin_files

    def load_plugin_from_file(
        self,
        file_path: str,
        auto_register: bool = True
    ) -> Optional[Type[SearchPlugin]]:
        """
        Load a plugin from a Python file.

        Args:
            file_path: Path to the plugin file
            auto_register: Automatically register the plugin

        Returns:
            Plugin class or None if loading failed
        """
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                raise PluginLoadError(f"Plugin file not found: {file_path}")

            # Generate module name from file name
            module_name = f"torq_plugins.{file_path_obj.stem}"

            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                raise PluginLoadError(f"Failed to load spec for {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find SearchPlugin subclasses in the module
            plugin_classes = self._find_plugin_classes(module)

            if not plugin_classes:
                self.logger.warning(f"[PLUGIN_LOADER] No plugin classes found in {file_path}")
                return None

            # Take the first plugin class found
            plugin_class = plugin_classes[0]

            # Validate the plugin
            if not self._validate_plugin_class(plugin_class):
                raise PluginLoadError(f"Plugin validation failed for {plugin_class.__name__}")

            # Register if requested
            if auto_register:
                success = self.registry.register(plugin_class, auto_initialize=True)
                if success:
                    self.loaded_plugins.append(file_path)
                    self.logger.info(f"[PLUGIN_LOADER] Loaded and registered plugin from {file_path}")
                else:
                    self.logger.error(f"[PLUGIN_LOADER] Failed to register plugin from {file_path}")

            return plugin_class

        except Exception as e:
            self.logger.error(f"[PLUGIN_LOADER] Error loading plugin from {file_path}: {e}")
            return None

    def load_all_plugins(self, plugin_dir: str) -> int:
        """
        Discover and load all plugins from a directory.

        Args:
            plugin_dir: Directory containing plugin files

        Returns:
            Number of successfully loaded plugins
        """
        plugin_files = self.discover_plugins(plugin_dir)
        loaded_count = 0

        for file_path in plugin_files:
            if self.load_plugin_from_file(file_path, auto_register=True):
                loaded_count += 1

        self.logger.info(f"[PLUGIN_LOADER] Loaded {loaded_count}/{len(plugin_files)} plugins from {plugin_dir}")
        return loaded_count

    def _find_plugin_classes(self, module) -> List[Type[SearchPlugin]]:
        """
        Find all SearchPlugin subclasses in a module.

        Args:
            module: Python module to search

        Returns:
            List of plugin classes found
        """
        plugin_classes = []

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            # Check if it's a class and subclass of SearchPlugin
            if (isinstance(attr, type) and
                issubclass(attr, SearchPlugin) and
                attr is not SearchPlugin):
                plugin_classes.append(attr)

        return plugin_classes

    def _validate_plugin_class(self, plugin_class: Type[SearchPlugin]) -> bool:
        """
        Validate that a plugin class implements required methods.

        Args:
            plugin_class: Plugin class to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if search method is implemented
            if not hasattr(plugin_class, 'search'):
                self.logger.error(f"[PLUGIN_LOADER] Plugin {plugin_class.__name__} missing 'search' method")
                return False

            # Try to create an instance
            instance = plugin_class()

            # Check if metadata is set
            metadata = instance.get_metadata()
            if not metadata:
                self.logger.warning(f"[PLUGIN_LOADER] Plugin {plugin_class.__name__} has no metadata")
                # Still valid, just warning

            return True

        except Exception as e:
            self.logger.error(f"[PLUGIN_LOADER] Plugin validation failed: {e}")
            return False

    def reload_plugin(self, plugin_name: str, file_path: str) -> bool:
        """
        Reload a plugin (useful for development).

        Args:
            plugin_name: Name of the plugin to reload
            file_path: Path to the plugin file

        Returns:
            True if reload successful, False otherwise
        """
        try:
            # Unregister existing plugin
            self.registry.unregister(plugin_name)

            # Remove from loaded plugins list
            if file_path in self.loaded_plugins:
                self.loaded_plugins.remove(file_path)

            # Load again
            plugin_class = self.load_plugin_from_file(file_path, auto_register=True)

            return plugin_class is not None

        except Exception as e:
            self.logger.error(f"[PLUGIN_LOADER] Error reloading plugin '{plugin_name}': {e}")
            return False

    def get_loaded_plugins(self) -> List[str]:
        """
        Get list of loaded plugin file paths.

        Returns:
            List of file paths
        """
        return self.loaded_plugins.copy()

    def unload_all(self):
        """Unload all loaded plugins."""
        for plugin_name in self.registry.list_plugins():
            self.registry.unregister(plugin_name)

        self.loaded_plugins.clear()
        self.logger.info("[PLUGIN_LOADER] All plugins unloaded")
