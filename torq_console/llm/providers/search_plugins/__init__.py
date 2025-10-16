"""
Search Plugins System for TORQ Console

Modular, extensible search plugin architecture allowing dynamic loading
of custom search sources without modifying core code.

Phase 3: Plugin Architecture Implementation
"""

from .base import SearchPlugin, PluginMetadata, SearchResult
from .registry import PluginRegistry, get_registry
from .loader import PluginLoader

__all__ = [
    'SearchPlugin',
    'PluginMetadata',
    'SearchResult',
    'PluginRegistry',
    'PluginLoader',
    'get_registry'
]

__version__ = '1.0.0'
