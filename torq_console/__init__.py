"""
TORQ CONSOLE - An enhanced evolution of Aider with MCP integration.

Version: 0.60.0 (MCP-Enhanced Polish Milestone)
Author: B Flowers
License: MIT
"""

__version__ = "0.60.0"
__author__ = "B Flowers"
__license__ = "MIT"

# Optional imports - only import if dependencies are available
_TorqConsole = None
_TorqConfig = None

def get_torq_console():
    """Get TorqConsole class with lazy import."""
    global _TorqConsole
    if _TorqConsole is None:
        from .core.console import TorqConsole
        _TorqConsole = TorqConsole
    return _TorqConsole

def get_torq_config():
    """Get TorqConfig class with lazy import."""
    global _TorqConfig
    if _TorqConfig is None:
        from .core.config import TorqConfig
        _TorqConfig = TorqConfig
    return _TorqConfig

# Make available for direct import when dependencies exist
try:
    from .core.console import TorqConsole
    from .core.config import TorqConfig
    __all__ = ["TorqConsole", "TorqConfig"]
except ImportError:
    # Dependencies not available, use lazy imports
    TorqConsole = get_torq_console
    TorqConfig = get_torq_config
    __all__ = ["TorqConsole", "TorqConfig", "get_torq_console", "get_torq_config"]