"""
Built-in Search Plugins for TORQ Console

This package contains official search plugins maintained by the TORQ team.
"""

from .reddit_plugin import RedditSearchPlugin
from .hackernews_plugin import HackerNewsSearchPlugin
from .arxiv_plugin import ArXivSearchPlugin

__all__ = [
    'RedditSearchPlugin',
    'HackerNewsSearchPlugin',
    'ArXivSearchPlugin'
]

# Plugin metadata for easy discovery
BUILTIN_PLUGINS = [
    RedditSearchPlugin,
    HackerNewsSearchPlugin,
    ArXivSearchPlugin
]
