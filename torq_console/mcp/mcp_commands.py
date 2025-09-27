"""
MCP Command Interface for TORQ Console following Claude Code patterns
"""
import asyncio
import json
from typing import Dict, Any, List
from .mcp_manager import TORQMCPManager

class MCPCommands:
    """Command interface for MCP management in TORQ Console"""

    def __init__(self, mcp_manager: TORQMCPManager):
        self.mcp_manager = mcp_manager

    async def handle_mcp_command(self, command: str, args: List[str]) -> str:
        """Handle MCP-related commands"""

        if command == "list":
            return await self._list_servers()
        elif command == "connect":
            return await self._connect_server(args)
        elif command == "disconnect":
            return await self._disconnect_server(args)
        elif command == "status":
            return await self._server_status()
        elif command == "tools":
            return await self._list_tools(args)
        elif command == "add":
            return await self._add_server(args)
        elif command == "remove":
            return await self._remove_server(args)
        elif command == "install":
            return await self._install_server(args)
        else:
            return self._help()

    async def _list_servers(self) -> str:
        """List all configured MCP servers"""
        servers = self.mcp_manager.servers
        status = await self.mcp_manager.get_server_status()

        if not servers:
            return "No MCP servers configured. Use '/mcp add' to add servers."

        result = "Configured MCP Servers:\n"
        for name, config in servers.items():
            server_status = status.get(name, "unknown")
            result += f"  • {name} ({config['type']}) - {server_status}\n"

        return result

    async def _connect_server(self, args: List[str]) -> str:
        """Connect to a specific server"""
        if not args:
            return "Usage: /mcp connect <server_name>"

        server_name = args[0]
        success = await self.mcp_manager.connect_server(server_name)

        if success:
            return f"PASS Connected to MCP server: {server_name}"
        else:
            return f"FAIL Failed to connect to MCP server: {server_name}"

    async def _disconnect_server(self, args: List[str]) -> str:
        """Disconnect from a specific server"""
        if not args:
            return "Usage: /mcp disconnect <server_name>"

        server_name = args[0]
        await self.mcp_manager.disconnect_server(server_name)
        return f"Disconnected from MCP server: {server_name}"

    async def _server_status(self) -> str:
        """Show status of all servers"""
        status = await self.mcp_manager.get_server_status()

        if not status:
            return "No MCP servers configured."

        result = "MCP Server Status:\n"
        for server, state in status.items():
            emoji = "ONLINE" if state == "connected" else "OFFLINE"
            result += f"  {emoji} {server}: {state}\n"

        return result

    async def _list_tools(self, args: List[str]) -> str:
        """List available tools from servers"""
        server_name = args[0] if args else None
        tools = await self.mcp_manager.list_available_tools(server_name)

        if not tools:
            return "No tools available. Connect to MCP servers first."

        result = "Available MCP Tools:\n"
        for server, tool_list in tools.items():
            result += f"\n{server}:\n"
            for tool in tool_list:
                result += f"  • {tool}\n"

        return result

    async def _add_server(self, args: List[str]) -> str:
        """Add a new MCP server configuration"""
        if len(args) < 2:
            return self._add_server_help()

        server_name = args[0]
        server_type = args[1]

        # Popular server templates
        templates = {
            "github": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}
            },
            "filesystem": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
            },
            "brave": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"}
            },
            "postgres": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres"],
                "env": {"POSTGRES_CONNECTION_STRING": "${POSTGRES_URL}"}
            },
            "sqlite": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"]
            }
        }

        if server_type in templates:
            config = templates[server_type]
            self.mcp_manager.add_server(server_name, config)
            return f"PASS Added {server_type} MCP server: {server_name}"
        else:
            return f"FAIL Unknown server type: {server_type}\nAvailable types: {list(templates.keys())}"

    async def _remove_server(self, args: List[str]) -> str:
        """Remove an MCP server configuration"""
        if not args:
            return "Usage: /mcp remove <server_name>"

        server_name = args[0]
        self.mcp_manager.remove_server(server_name)
        return f"Removed MCP server: {server_name}"

    async def _install_server(self, args: List[str]) -> str:
        """Install an MCP server package"""
        if not args:
            return "Usage: /mcp install <package_name>"

        package_name = args[0]

        # Install the npm package
        process = await asyncio.create_subprocess_exec(
            "npm", "install", "-g", package_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return f"PASS Installed MCP server package: {package_name}"
        else:
            return f"FAIL Failed to install {package_name}: {stderr.decode()}"

    def _add_server_help(self) -> str:
        """Help for adding servers"""
        return """Usage: /mcp add <name> <type>

Available server types:
  • github      - GitHub integration
  • filesystem  - File system access
  • brave       - Brave Search API
  • postgres    - PostgreSQL database
  • sqlite      - SQLite database

Example: /mcp add my-github github"""

    def _help(self) -> str:
        """MCP help text"""
        return """TORQ Console MCP Commands:

  /mcp list                    - List configured servers
  /mcp status                  - Show server connection status
  /mcp connect <server>        - Connect to a server
  /mcp disconnect <server>     - Disconnect from a server
  /mcp tools [server]          - List available tools
  /mcp add <name> <type>       - Add server configuration
  /mcp remove <name>           - Remove server configuration
  /mcp install <package>       - Install MCP server package

Popular MCP Servers:
  • @modelcontextprotocol/server-github
  • @modelcontextprotocol/server-filesystem
  • @modelcontextprotocol/server-brave-search
  • @modelcontextprotocol/server-postgres
  • @modelcontextprotocol/server-sqlite"""