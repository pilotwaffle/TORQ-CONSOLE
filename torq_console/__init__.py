"""
TORQ CONSOLE - Enhanced AI pair programmer with MCP integration.

Combines the speed of Aider with the polish of Cursor, enhanced with
Model Context Protocol (MCP) for agentic workflows and Claude Code compatibility.
"""

__version__ = "1.0.0"
__author__ = "B Flowers"
__email__ = "flowers@example.com"

from .core.console import TorqConsole
from .core.config import TorqConfig
from .mcp.client import MCPClient
from .ui.shell import InteractiveShell
from .utils.git_manager import GitManager

__all__ = [
    "torq_console.core.console.TorqConsole",
    "torq_console.core.config.TorqConfig",
    "torq_console.llm.manager.LLMManager",
    "torq_console.llm.providers.claude.ClaudeProvider",
    "torq_console.llm.providers.deepseek.DeepSeekProvider",
    "torq_console.llm.providers.ollama.OllamaProvider",
    "torq_console.llm.providers.llama_cpp_provider.LlamaCppQualityProvider",
    "torq_console.llm.providers.websearch.WebSearchProvider",
    "TorqConsole",
    "TorqConfig",
    "MCPClient",
    "InteractiveShell",
    "GitManager",
]# Trigger cache update
