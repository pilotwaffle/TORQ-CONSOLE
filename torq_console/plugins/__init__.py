"""
TORQ Console Plugin System

Extensible plugin architecture allowing dynamic loading of custom extensions
for agents, commands, UI components, and integrations.
"""

from .manager import PluginManager
from .base import TORQPlugin, PluginMetadata, PluginHook, PluginCapability
from .loader import PluginLoader
from .registry import PluginRegistry

__all__ = [
    'PluginManager',
    'TORQPlugin',
    'PluginMetadata',
    'PluginHook',
    'PluginCapability',
    'PluginLoader',
    'PluginRegistry'
]

__version__ = '1.0.0'
