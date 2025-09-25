"""MCP integration for TORQ CONSOLE."""

from .client import MCPClient
from .claude_code_bridge import ClaudeCodeBridge

__all__ = ["MCPClient", "ClaudeCodeBridge"]