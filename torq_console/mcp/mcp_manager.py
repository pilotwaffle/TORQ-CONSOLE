"""
Enhanced MCP Manager for TORQ Console following Claude Code best practices
"""
import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class TORQMCPManager:
    """Enhanced MCP manager following Claude Code patterns"""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger("TORQ.MCP")
        self.config_path = config_path or os.path.join(
            os.path.expanduser("~"), ".torq_console", "mcp_config.json"
        )
        self.servers = {}
        self.active_connections = {}

    async def load_config(self):
        """Load MCP server configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.servers = config.get('servers', {})
                    self.logger.info(f"Loaded {len(self.servers)} MCP server configs")
            else:
                # Create default config
                await self.create_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load MCP config: {e}")

    async def create_default_config(self):
        """Create default MCP configuration following Claude Code patterns"""
        default_config = {
            "servers": {
                "github": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
                    }
                },
                "filesystem": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
                },
                "brave_search": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                    "env": {
                        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
                    }
                },
                "postgres": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-postgres"],
                    "env": {
                        "POSTGRES_CONNECTION_STRING": "${POSTGRES_URL}"
                    }
                }
            }
        }

        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        self.logger.info(f"Created default MCP config at {self.config_path}")
        self.servers = default_config['servers']

    async def connect_server(self, server_name: str) -> bool:
        """Connect to an MCP server"""
        if server_name not in self.servers:
            self.logger.error(f"Server {server_name} not configured")
            return False

        server_config = self.servers[server_name]

        try:
            if server_config['type'] == 'stdio':
                # Handle Windows command execution
                command = server_config['command']
                if os.name == 'nt' and command == 'npx':
                    command = 'npx.cmd'

                # Start stdio server process
                process = await asyncio.create_subprocess_exec(
                    command,
                    *server_config['args'],
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, **server_config.get('env', {})}
                )

                self.active_connections[server_name] = {
                    'type': 'stdio',
                    'process': process,
                    'config': server_config
                }

                self.logger.info(f"Connected to MCP server: {server_name}")
                return True

            elif server_config['type'] == 'sse':
                # SSE server connection logic
                # Implementation for Server-Sent Events
                pass

            elif server_config['type'] == 'http':
                # HTTP server connection logic
                # Implementation for HTTP requests
                pass

        except Exception as e:
            self.logger.error(f"Failed to connect to {server_name}: {e}")
            return False

        return False

    async def disconnect_server(self, server_name: str):
        """Disconnect from an MCP server"""
        if server_name in self.active_connections:
            connection = self.active_connections[server_name]

            if connection['type'] == 'stdio' and 'process' in connection:
                connection['process'].terminate()
                await connection['process'].wait()

            del self.active_connections[server_name]
            self.logger.info(f"Disconnected from MCP server: {server_name}")

    async def list_available_tools(self, server_name: str = None) -> Dict[str, List[str]]:
        """List available tools from connected servers"""
        tools = {}

        servers_to_check = [server_name] if server_name else list(self.active_connections.keys())

        for server in servers_to_check:
            if server in self.active_connections:
                # Query server for available tools
                # This would involve MCP protocol communication
                tools[server] = ["placeholder_tool"]  # Replace with actual tool discovery

        return tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server"""
        if server_name not in self.active_connections:
            raise ValueError(f"Server {server_name} not connected")

        # Implement MCP protocol tool calling
        # This would involve JSON-RPC communication with the server
        pass

    async def get_server_status(self) -> Dict[str, str]:
        """Get status of all configured servers"""
        status = {}

        for server_name in self.servers:
            if server_name in self.active_connections:
                status[server_name] = "connected"
            else:
                status[server_name] = "disconnected"

        return status

    async def auto_connect_servers(self):
        """Auto-connect to all configured servers"""
        for server_name in self.servers:
            await self.connect_server(server_name)

    async def shutdown(self):
        """Shutdown all MCP connections"""
        for server_name in list(self.active_connections.keys()):
            await self.disconnect_server(server_name)

    def add_server(self, name: str, config: Dict[str, Any]):
        """Add a new MCP server configuration"""
        self.servers[name] = config

        # Save to config file
        full_config = {"servers": self.servers}
        with open(self.config_path, 'w') as f:
            json.dump(full_config, f, indent=2)

        self.logger.info(f"Added MCP server configuration: {name}")

    def remove_server(self, name: str):
        """Remove an MCP server configuration"""
        if name in self.servers:
            del self.servers[name]

            # Save to config file
            full_config = {"servers": self.servers}
            with open(self.config_path, 'w') as f:
                json.dump(full_config, f, indent=2)

            self.logger.info(f"Removed MCP server configuration: {name}")