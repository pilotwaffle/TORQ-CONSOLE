"""
TORQ CONSOLE - Enhanced AI pair programmer with MCP integration.

Combines the speed of Aider with the polish of Cursor, enhanced with
Model Context Protocol (MCP) for agentic workflows and Claude Code compatibility.
"""

__version__ = "0.70.0"
__author__ = "B Flowers"
__email__ = "flowers@example.com"

from .core.console import TorqConsole
from .core.config import TorqConfig
from .mcp.client import MCPClient
from .ui.shell import InteractiveShell
from .utils.git_manager import GitManager

__all__ = [
    "TorqConsole",
    "TorqConfig",
    "MCPClient",
    "InteractiveShell",
    "GitManager",
]