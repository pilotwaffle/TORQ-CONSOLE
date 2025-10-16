"""
Base SearchPlugin Class

Defines the interface that all search plugins must implement.
Provides standard structure for search results and plugin metadata.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging


@dataclass
class SearchResult:
    """
    Standard search result structure.

    All plugins must return results in this format for consistency.
    """
    title: str
    snippet: str
    url: str
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Optional fields
    author: Optional[str] = None
    date_published: Optional[str] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'title': self.title,
            'snippet': self.snippet,
            'url': self.url,
            'source': self.source,
            'timestamp': self.timestamp,
            'author': self.author,
            'date_published': self.date_published,
            'score': self.score,
            'metadata': self.metadata
        }


@dataclass
class PluginMetadata:
    """
    Plugin metadata and configuration.

    Provides information about the plugin for discovery and management.
    """
    name: str
    version: str
    description: str
    author: str

    # Plugin capabilities
    supports_news: bool = False
    supports_academic: bool = False
    supports_general: bool = True

    # Requirements
    requires_api_key: bool = False
    api_key_env_var: Optional[str] = None

    # Rate limiting
    max_requests_per_minute: int = 10
    max_requests_per_hour: int = 100

    # Additional metadata
    homepage: Optional[str] = None
    documentation: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'supports_news': self.supports_news,
            'supports_academic': self.supports_academic,
            'supports_general': self.supports_general,
            'requires_api_key': self.requires_api_key,
            'api_key_env_var': self.api_key_env_var,
            'max_requests_per_minute': self.max_requests_per_minute,
            'max_requests_per_hour': self.max_requests_per_hour,
            'homepage': self.homepage,
            'documentation': self.documentation,
            'tags': self.tags
        }


class SearchPlugin(ABC):
    """
    Abstract base class for search plugins.

    All search plugins must inherit from this class and implement
    the required abstract methods.

    Example:
        class RedditSearchPlugin(SearchPlugin):
            def __init__(self):
                super().__init__()
                self.metadata = PluginMetadata(
                    name="reddit",
                    version="1.0.0",
                    description="Search Reddit posts and comments",
                    author="TORQ Team"
                )

            async def search(self, query, max_results, search_type):
                # Implementation here
                pass
    """

    def __init__(self):
        """Initialize the plugin."""
        self.logger = logging.getLogger(f"plugin.{self.__class__.__name__}")
        self.metadata: Optional[PluginMetadata] = None
        self._initialized = False

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "general"
    ) -> List[SearchResult]:
        """
        Perform search using this plugin.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_type: Type of search (general, news, academic)

        Returns:
            List of SearchResult objects

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement search()")

    async def initialize(self) -> bool:
        """
        Initialize the plugin.

        Called once when the plugin is loaded. Use this for:
        - Loading configuration
        - Validating API keys
        - Setting up connections

        Returns:
            True if initialization successful, False otherwise
        """
        self._initialized = True
        return True

    async def cleanup(self):
        """
        Cleanup resources.

        Called when the plugin is unloaded or the system shuts down.
        Use this to close connections, save state, etc.
        """
        self._initialized = False

    def is_available(self) -> bool:
        """
        Check if plugin is available and ready to use.

        Returns:
            True if plugin can be used, False otherwise
        """
        return self._initialized

    def supports_search_type(self, search_type: str) -> bool:
        """
        Check if plugin supports a specific search type.

        Args:
            search_type: Type of search (general, news, academic)

        Returns:
            True if supported, False otherwise
        """
        if not self.metadata:
            return search_type == "general"

        if search_type == "news":
            return self.metadata.supports_news
        elif search_type == "academic":
            return self.metadata.supports_academic
        else:
            return self.metadata.supports_general

    def get_metadata(self) -> Optional[PluginMetadata]:
        """
        Get plugin metadata.

        Returns:
            PluginMetadata object or None if not set
        """
        return self.metadata

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.

        Override this method to add custom validation logic.

        Args:
            config: Configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        return True

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the plugin.

        Override this method to add custom health checks.

        Returns:
            Dictionary with health check results
        """
        return {
            'status': 'healthy' if self.is_available() else 'unavailable',
            'initialized': self._initialized,
            'plugin': self.metadata.name if self.metadata else 'unknown'
        }


class SearchPluginError(Exception):
    """Base exception for search plugin errors."""
    pass


class PluginNotFoundError(SearchPluginError):
    """Raised when a plugin is not found."""
    pass


class PluginLoadError(SearchPluginError):
    """Raised when a plugin fails to load."""
    pass


class PluginInitializationError(SearchPluginError):
    """Raised when plugin initialization fails."""
    pass
