"""
Plugin Loader for TORQ Console

Discovers, validates, and loads plugins from multiple sources.
"""

import os
import sys
import importlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import TORQPlugin, PluginMetadata


class PluginLoader:
    """Discovers and loads TORQ Console plugins."""

    def __init__(self, plugin_paths: Optional[List[str]] = None):
        """
        Initialize plugin loader.

        Args:
            plugin_paths: List of directories to search for plugins
        """
        self.logger = logging.getLogger(__name__)
        self.plugin_paths = plugin_paths or self._default_plugin_paths()
        self.loaded_plugins: Dict[str, TORQPlugin] = {}

    def _default_plugin_paths(self) -> List[str]:
        """Get default plugin search paths."""
        paths = []

        # User plugins directory
        user_plugin_dir = Path.home() / ".torq_console" / "plugins"
        if user_plugin_dir.exists():
            paths.append(str(user_plugin_dir))

        # Project-local plugins directory
        project_plugin_dir = Path.cwd() / "plugins"
        if project_plugin_dir.exists() and str(project_plugin_dir) not in paths:
            paths.append(str(project_plugin_dir))

        # Built-in plugins
        builtin_dir = Path(__file__).parent / "builtin"
        if builtin_dir.exists():
            paths.append(str(builtin_dir))

        return paths

    def discover(self) -> List[Path]:
        """
        Discover all potential plugins in search paths.

        Returns:
            List of directories containing plugins
        """
        discovered = []

        for plugin_path in self.plugin_paths:
            plugin_dir = Path(plugin_path)
            if not plugin_dir.exists():
                continue

            # Look for plugin.json or __init__.py
            for item in plugin_dir.iterdir():
                if item.is_dir():
                    # Check for plugin manifest
                    manifest = item / "plugin.json"
                    init_file = item / "__init__.py"

                    if manifest.exists() or init_file.exists():
                        discovered.append(item)
                    elif (item / "plugin.py").exists():
                        discovered.append(item)

        self.logger.info(f"Discovered {len(discovered)} potential plugins")
        return discovered

    def load_from_directory(self, plugin_dir: Path) -> Optional[TORQPlugin]:
        """
        Load a plugin from a directory.

        Args:
            plugin_dir: Directory containing the plugin

        Returns:
            Loaded plugin instance or None if loading failed
        """
        plugin_name = plugin_dir.name

        try:
            # Try importing as a Python package
            sys.path.insert(0, str(plugin_dir.parent))

            if (plugin_dir / "__init__.py").exists():
                module = importlib.import_module(f"{plugin_name}")
            elif (plugin_dir / "plugin.py").exists():
                spec = importlib.util.spec_from_file_location(f"{plugin_name}.plugin", plugin_dir / "plugin.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                self.logger.warning(f"No valid entry point for plugin {plugin_name}")
                return None

            # Find plugin class
            plugin_class = self._find_plugin_class(module, plugin_name)
            if plugin_class:
                plugin_instance = plugin_class()
                self.loaded_plugins[plugin_name] = plugin_instance
                self.logger.info(f"Loaded plugin: {plugin_name}")
                return plugin_instance

        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return None

    def _find_plugin_class(self, module, plugin_name: str) -> Optional[type]:
        """Find the plugin class in a module."""
        # Try common class names
        for attr_name in [f"{plugin_name.capitalize()}Plugin", f"{plugin_name}Plugin", "Plugin"]:
            if hasattr(module, attr_name):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, TORQPlugin):
                    return attr

        # Check for get_plugin() function
        if hasattr(module, "get_plugin"):
            get_plugin = getattr(module, "get_plugin")
            if callable(get_plugin):
                plugin = get_plugin()
                if isinstance(plugin, TORQPlugin):
                    return plugin.__class__

        return None

    def load_all(self) -> Dict[str, TORQPlugin]:
        """
        Discover and load all plugins.

        Returns:
            Dictionary mapping plugin names to plugin instances
        """
        discovered = self.discover()

        for plugin_dir in discovered:
            plugin = self.load_from_directory(plugin_dir)
            if plugin:
                self.loaded_plugins[plugin.metadata.name] = plugin

        self.logger.info(f"Successfully loaded {len(self.loaded_plugins)} plugins")
        return self.loaded_plugins

    def get_plugin(self, name: str) -> Optional[TORQPlugin]:
        """
        Get a specific loaded plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self.loaded_plugins.get(name)

    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin by name.

        Args:
            name: Plugin name

        Returns:
            True if unloaded successfully
        """
        if name in self.loaded_plugins:
            plugin = self.loaded_plugins[name]
            try:
                plugin.shutdown()
                del self.loaded_plugins[name]
                self.logger.info(f"Unloaded plugin: {name}")
                return True
            except Exception as e:
                self.logger.error(f"Error unloading plugin {name}: {e}")
                return False
        return False
