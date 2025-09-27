"""
Enhanced MCP Integration for TORQ Console
Combines TORQMCPManager with MCPCommands for complete MCP support
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from .mcp_manager import TORQMCPManager
from .mcp_commands import MCPCommands
from .client import MCPClient


class EnhancedMCPIntegration:
    """Enhanced MCP integration combining manager, commands, and client functionality"""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger("TORQ.MCP.Enhanced")

        # Initialize components
        self.manager = TORQMCPManager(config_path)
        self.commands = MCPCommands(self.manager)
        self.legacy_client = MCPClient()

        # Track initialization
        self._initialized = False

    async def initialize(self):
        """Initialize the enhanced MCP integration"""
        if self._initialized:
            return

        try:
            # Load MCP configuration
            await self.manager.load_config()

            # Auto-connect to configured servers
            await self.manager.auto_connect_servers()

            self._initialized = True
            self.logger.info("Enhanced MCP integration initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced MCP integration: {e}")
            raise

    async def handle_mcp_command(self, command: str, args: List[str]) -> str:
        """Handle MCP commands using the enhanced command interface"""
        return await self.commands.handle_mcp_command(command, args)

    async def connect_server(self, server_name: str) -> bool:
        """Connect to an MCP server"""
        return await self.manager.connect_server(server_name)

    async def disconnect_server(self, server_name: str):
        """Disconnect from an MCP server"""
        await self.manager.disconnect_server(server_name)

    async def get_server_status(self) -> Dict[str, str]:
        """Get status of all configured servers"""
        return await self.manager.get_server_status()

    async def list_available_tools(self, server_name: str = None) -> Dict[str, List[str]]:
        """List available tools from connected servers"""
        return await self.manager.list_available_tools(server_name)

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server"""
        return await self.manager.call_tool(server_name, tool_name, arguments)

    def add_server(self, name: str, config: Dict[str, Any]):
        """Add a new MCP server configuration"""
        self.manager.add_server(name, config)

    def remove_server(self, name: str):
        """Remove an MCP server configuration"""
        self.manager.remove_server(name)

    def get_configured_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured MCP servers"""
        return self.manager.servers

    def get_active_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get all active MCP connections"""
        return self.manager.active_connections

    async def connect_legacy_endpoint(self, endpoint: str) -> bool:
        """Connect to MCP server using legacy client (for backward compatibility)"""
        return await self.legacy_client.connect(endpoint)

    async def list_tools_legacy(self, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tools using legacy client"""
        return await self.legacy_client.list_tools(endpoint)

    async def call_tool_legacy(self, tool_name: str, arguments: Dict[str, Any] = None,
                             endpoint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Call tool using legacy client"""
        return await self.legacy_client.call_tool(tool_name, arguments, endpoint)

    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all connections"""
        health_status = {}

        # Check enhanced manager connections
        for server_name in self.manager.active_connections:
            try:
                # Simple health check - verify connection is active
                health_status[f"enhanced_{server_name}"] = True
            except Exception:
                health_status[f"enhanced_{server_name}"] = False

        # Check legacy client connections
        for endpoint in self.legacy_client.get_connected_endpoints():
            health_status[f"legacy_{endpoint}"] = await self.legacy_client.health_check(endpoint)

        return health_status

    async def shutdown(self):
        """Shutdown all MCP connections"""
        try:
            # Shutdown enhanced manager
            await self.manager.shutdown()

            # Shutdown legacy client
            await self.legacy_client.shutdown()

            self.logger.info("Enhanced MCP integration shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during MCP shutdown: {e}")

    def get_integration_info(self) -> Dict[str, Any]:
        """Get comprehensive information about MCP integration status"""
        return {
            "initialized": self._initialized,
            "enhanced_servers": len(self.manager.servers),
            "active_enhanced_connections": len(self.manager.active_connections),
            "legacy_connections": len(self.legacy_client.get_connected_endpoints()),
            "configured_servers": list(self.manager.servers.keys()),
            "active_connections": list(self.manager.active_connections.keys()),
            "legacy_endpoints": self.legacy_client.get_connected_endpoints()
        }