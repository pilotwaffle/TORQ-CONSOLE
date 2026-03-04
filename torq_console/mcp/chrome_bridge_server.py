"""
TORQ Chrome Bridge - MCP Server for Claude Code

This MCP server exposes browser automation tools to Claude Code via the
Model Context Protocol, enabling Claude to control Chrome for:
- Deployment verification
- Screenshot capture
- UI testing
- Form automation
- Multi-step workflows

Installation:
    Add to ~/.claude/mcp.json or .claude/mcp.json:

    {
      "mcpServers": {
        "chrome-bridge": {
          "command": "python",
          "args": ["E:/TORQ-CONSOLE/torq_console/mcp/chrome_bridge_server.py"],
          "env": {
            "CHROME_BRIDGE_URL": "http://127.0.0.1:4545",
            "CHROME_BRIDGE_API_KEY": "your-api-key"
          }
        }
      }
    }

Usage in Claude Code:
    "Navigate to https://example.com and take a screenshot"
    "Verify the Railway deployment at https://web-production.up.railway.app/health"
    "Extract the title from the current page"
"""
import asyncio
import json
import os
import sys
from typing import Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    # Fallback for when MCP is not installed
    Server = None

from torq_console.tools.chrome_operator import (
    ChromeOperator,
    ChromeConnectionError,
    ChromeExecutionError,
    ChromeApprovalRequired,
)

# Configuration
CHROME_BRIDGE_URL = os.getenv("CHROME_BRIDGE_URL", "http://127.0.0.1:4545")
CHROME_BRIDGE_API_KEY = os.getenv("CHROME_BRIDGE_API_KEY", "")
DEFAULT_REQUIRE_APPROVAL = os.getenv("CHROME_BRIDGE_REQUIRE_APPROVAL", "true").lower() == "true"


class ChromeBridgeMCPServer:
    """MCP Server for TORQ Chrome Bridge."""

    def __init__(self):
        self.server = Server("chrome-bridge")
        self.chrome: ChromeOperator = None
        self.session_id: str = None

        if HAS_MCP:
            self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available browser automation tools."""
            return [
                Tool(
                    name="chrome_navigate",
                    description="Navigate to a URL in Chrome",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to navigate to"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="chrome_click",
                    description="Click an element on the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the element"
                            },
                            "by": {
                                "type": "string",
                                "enum": ["css", "id", "name", "xpath"],
                                "description": "Selector type (default: css)"
                            }
                        },
                        "required": ["selector"]
                    }
                ),
                Tool(
                    name="chrome_type",
                    description="Type text into an input field",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the input"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text to type"
                            },
                            "by": {
                                "type": "string",
                                "enum": ["css", "id", "name", "xpath"],
                                "description": "Selector type (default: css)"
                            }
                        },
                        "required": ["selector", "text"]
                    }
                ),
                Tool(
                    name="chrome_extract",
                    description="Extract data from an element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the element"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["text", "html", "value", "href", "src"],
                                "description": "Extraction mode (default: text)"
                            },
                            "by": {
                                "type": "string",
                                "enum": ["css", "id", "name", "xpath"],
                                "description": "Selector type (default: css)"
                            }
                        },
                        "required": ["selector"]
                    }
                ),
                Tool(
                    name="chrome_screenshot",
                    description="Capture a screenshot of the current tab",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "full_page": {
                                "type": "boolean",
                                "description": "Capture full page (default: false, visible only)"
                            }
                        }
                    }
                ),
                Tool(
                    name="chrome_get_title",
                    description="Get the current page title",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="chrome_get_url",
                    description="Get the current page URL",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="chrome_wait",
                    description="Wait for a condition",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ms": {
                                "type": "number",
                                "description": "Milliseconds to wait"
                            },
                            "selector": {
                                "type": "string",
                                "description": "Wait for element to appear"
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Timeout in ms (default: 5000)"
                            }
                        }
                    }
                ),
                Tool(
                    name="chrome_verify_deployment",
                    description="Verify a web deployment (navigate + screenshot + health check)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Deployment URL to verify"
                            },
                            "expected_text": {
                                "type": "string",
                                "description": "Text that should be present on the page"
                            },
                            "expected_sha": {
                                "type": "string",
                                "description": "Expected git SHA (for health endpoints)"
                            },
                            "screenshot": {
                                "type": "boolean",
                                "description": "Capture screenshot (default: true)"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="chrome_execute_workflow",
                    description="Execute a multi-step browser workflow",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "actions": {
                                "type": "array",
                                "description": "List of actions to execute",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "op": {
                                            "type": "string",
                                            "enum": ["navigate", "click", "type", "extract", "screenshot", "wait", "get_title", "get_url"],
                                            "description": "Operation to perform"
                                        },
                                        "selector": {"type": "string"},
                                        "text": {"type": "string"},
                                        "url": {"type": "string"},
                                        "ms": {"type": "number"},
                                        "mode": {"type": "string"}
                                    }
                                }
                            },
                            "description": {
                                "type": "string",
                                "description": "Workflow description"
                            }
                        },
                        "required": ["actions"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls."""
            return await self.execute_tool(name, arguments)

    async def ensure_connection(self):
        """Ensure Chrome operator is connected and session is created."""
        if self.chrome is None:
            self.chrome = ChromeOperator(
                bridge_url=CHROME_BRIDGE_URL,
                api_key=CHROME_BRIDGE_API_KEY,
                default_require_approval=DEFAULT_REQUIRE_APPROVAL,
            )

            # Check health
            try:
                health = await self.chrome.health_check()
                print(f"[Chrome MCP] Connected to bridge: {health['service']}", file=sys.stderr)
            except ChromeConnectionError as e:
                return [{"error": f"Failed to connect to Chrome Bridge: {e}"}]

        if self.session_id is None:
            try:
                session = await self.chrome.create_session(
                    metadata={"source": "claude_code_mcp"}
                )
                self.session_id = session.session_id
                print(f"[Chrome MCP] Session created: {self.session_id}", file=sys.stderr)
            except ChromeConnectionError as e:
                return [{"error": f"Failed to create session: {e}"}]

    async def execute_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Execute a browser automation tool."""
        await self.ensure_connection()

        try:
            match name:
                case "chrome_navigate":
                    result = await self.chrome.act(self.session_id, [
                        {"op": "navigate", "url": arguments["url"]}
                    ])

                case "chrome_click":
                    result = await self.chrome.act(self.session_id, [
                        {"op": "click", "selector": arguments["selector"], "by": arguments.get("by", "css")}
                    ])

                case "chrome_type":
                    result = await self.chrome.act(self.session_id, [
                        {"op": "type", "selector": arguments["selector"], "text": arguments["text"], "by": arguments.get("by", "css")}
                    ])

                case "chrome_extract":
                    result = await self.chrome.act(self.session_id, [
                        {"op": "extract", "selector": arguments["selector"], "mode": arguments.get("mode", "text"), "by": arguments.get("by", "css")}
                    ])

                case "chrome_screenshot":
                    result = await self.chrome.act(self.session_id, [{"op": "screenshot"}])

                case "chrome_get_title":
                    result = await self.chrome.act(self.session_id, [{"op": "get_title"}])

                case "chrome_get_url":
                    result = await self.chrome.act(self.session_id, [{"op": "get_url"}])

                case "chrome_wait":
                    if "ms" in arguments:
                        result = await self.chrome.act(self.session_id, [
                            {"op": "wait", "ms": arguments["ms"]}
                        ])
                    else:
                        result = await self.chrome.act(self.session_id, [
                            {"op": "wait", "selector": arguments["selector"], "timeout_ms": arguments.get("timeout", 5000)}
                        ])

                case "chrome_verify_deployment":
                    url = arguments["url"]
                    expected_text = arguments.get("expected_text")
                    expected_sha = arguments.get("expected_sha")
                    screenshot = arguments.get("screenshot", True)

                    from torq_console.tools.chrome_operator import verify_deployment
                    result = await verify_deployment(url, expected_sha, expected_text, screenshot)

                case "chrome_execute_workflow":
                    result = await self.chrome.act(self.session_id, arguments["actions"])

                case _:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

            # Format result
            return self.format_result(result)

        except ChromeApprovalRequired as e:
            return [TextContent(type="text", text=(
                f"Browser session requires approval.\n"
                f"Session ID: {e.session_id}\n"
                f"Please approve in the Chrome extension popup, then retry."
            ))]

        except ChromeExecutionError as e:
            return [TextContent(type="text", text=f"Execution failed: {e}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]

    def format_result(self, result) -> list[TextContent]:
        """Format execution result for Claude."""
        parts = []

        # Status
        if result.ok:
            parts.append(TextContent(type="text", text="✓ Browser operation completed"))
        else:
            parts.append(TextContent(type="text", text=f"✗ Browser operation failed"))

        # Results
        for r in result.results:
            if r.status == "ok":
                if r.data:
                    parts.append(TextContent(type="text", text=f"  {r.op}: {r.data}"))
                else:
                    parts.append(TextContent(type="text", text=f"  {r.op}: OK"))
            else:
                parts.append(TextContent(type="text", text=f"  {r.op}: {r.status} ({r.error})"))

        # Screenshot
        if result.artifacts.get("screenshot_png_data_url"):
            parts.append(TextContent(type="text", text="  Screenshot captured (data URL)"))

        # Errors
        for err in result.errors:
            parts.append(TextContent(type="text", text=f"  Error: {err}"))

        return parts

    async def run(self):
        """Run the MCP server."""
        if not HAS_MCP:
            print("[ERROR] MCP SDK not installed. Install with:", file=sys.stderr)
            print("  pip install mcp", file=sys.stderr)
            sys.exit(1)

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="chrome-bridge",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point."""
    print("[Chrome MCP] Starting TORQ Chrome Bridge MCP Server", file=sys.stderr)
    print(f"[Chrome MCP] Bridge URL: {CHROME_BRIDGE_URL}", file=sys.stderr)
    print(f"[Chrome MCP] Require approval: {DEFAULT_REQUIRE_APPROVAL}", file=sys.stderr)

    server = ChromeBridgeMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
