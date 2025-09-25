"""
Enhanced MCP Client for TORQ Console - Claude Code Compatible.

Provides advanced MCP server integration with auto-discovery, dynamic tool registration,
health monitoring, and swarm agent integration for Claude Code compatibility.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from pathlib import Path
import httpx

from .client import MCPClient


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""
    server_id: str
    endpoint: str
    name: str = ""
    version: str = ""
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    prompts: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "disconnected"  # disconnected, connecting, connected, error
    last_health_check: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 5
    connection_attempts: int = 0
    max_connection_attempts: int = 3


class EnhancedMCPClient:
    """
    Enhanced MCP Client with advanced features for Claude Code compatibility.

    Features:
    - Auto-discovery of MCP servers with retry logic
    - Dynamic tool registration and proxying
    - Health monitoring and failover
    - Integration with TORQ Console swarm agents
    - Tool availability caching and optimization
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_client = MCPClient()

        # Server management
        self.servers: Dict[str, MCPServerInfo] = {}
        self.available_tools: Dict[str, str] = {}  # tool_name -> server_id
        self.tool_cache: Dict[str, Dict[str, Any]] = {}

        # Discovery and health monitoring
        self.discovery_enabled = True
        self.health_check_interval = timedelta(minutes=5)
        self.auto_reconnect = True
        self.last_discovery = None

        # Default server endpoints to discover
        self.default_endpoints = [
            "http://localhost:3100",
            "http://localhost:3101",
            "http://localhost:3102",
            "http://localhost:3103",
            "http://localhost:3104"
        ]

        # Tool proxying callbacks
        self.tool_handlers: Dict[str, Callable] = {}

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the enhanced MCP client with discovery and health monitoring.

        Returns:
            Initialization results with server status
        """
        start_time = datetime.now()

        self.logger.info("Initializing Enhanced MCP Client")

        try:
            # Discover and connect to available servers
            discovery_results = await self.discover_servers()

            # Start health monitoring
            if self.servers:
                asyncio.create_task(self._health_monitor_loop())

            initialization_time = (datetime.now() - start_time).total_seconds()

            return {
                'success': True,
                'servers_discovered': len(self.servers),
                'servers_connected': len([s for s in self.servers.values() if s.status == 'connected']),
                'tools_available': len(self.available_tools),
                'initialization_time_ms': round(initialization_time * 1000, 2),
                'servers': {sid: s.status for sid, s in self.servers.items()}
            }

        except Exception as e:
            self.logger.error(f"MCP client initialization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'servers_discovered': 0,
                'servers_connected': 0,
                'tools_available': 0
            }

    async def discover_servers(self, additional_endpoints: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Discover available MCP servers from known endpoints.

        Args:
            additional_endpoints: Extra endpoints to check beyond defaults

        Returns:
            Discovery results summary
        """
        endpoints = self.default_endpoints.copy()
        if additional_endpoints:
            endpoints.extend(additional_endpoints)

        discovery_results = {
            'servers_found': 0,
            'servers_connected': 0,
            'endpoints_checked': len(endpoints),
            'discovery_time': datetime.now()
        }

        self.logger.info(f"Discovering MCP servers from {len(endpoints)} endpoints")

        # Check each endpoint
        discovery_tasks = [
            self._discover_single_server(endpoint)
            for endpoint in endpoints
        ]

        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            endpoint = endpoints[i]

            if isinstance(result, Exception):
                self.logger.debug(f"Discovery failed for {endpoint}: {result}")
                continue

            if result and result.get('success'):
                server_info = result['server_info']
                self.servers[server_info.server_id] = server_info
                discovery_results['servers_found'] += 1

                if server_info.status == 'connected':
                    discovery_results['servers_connected'] += 1

                    # Register tools from this server
                    await self._register_server_tools(server_info)

        self.last_discovery = datetime.now()

        self.logger.info(f"Discovery complete: {discovery_results['servers_found']} servers found, "
                        f"{discovery_results['servers_connected']} connected")

        return discovery_results

    async def _discover_single_server(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Discover a single MCP server at the given endpoint."""
        server_id = f"mcp_{endpoint.replace('://', '_').replace(':', '_').replace('/', '_')}"

        try:
            # Try to connect to the server
            connected = await self.base_client.connect(endpoint)

            if not connected:
                return None

            # Get server capabilities
            server_info = MCPServerInfo(
                server_id=server_id,
                endpoint=endpoint,
                status='connected' if connected else 'error'
            )

            # Try to get server info
            try:
                # Get available tools
                tools = await self.base_client.list_tools(endpoint)
                if tools and 'tools' in tools:
                    server_info.tools = tools['tools']
                    server_info.capabilities.append('tools')

                # Get available resources
                resources = await self.base_client.list_resources(endpoint)
                if resources and 'resources' in resources:
                    server_info.resources = resources['resources']
                    server_info.capabilities.append('resources')

                # Get available prompts
                prompts = await self.base_client.list_prompts(endpoint)
                if prompts and 'prompts' in prompts:
                    server_info.prompts = prompts['prompts']
                    server_info.capabilities.append('prompts')

                server_info.last_health_check = datetime.now()

            except Exception as e:
                self.logger.debug(f"Could not get capabilities for {endpoint}: {e}")

            return {
                'success': True,
                'server_info': server_info
            }

        except Exception as e:
            self.logger.debug(f"Failed to discover server at {endpoint}: {e}")
            return None

    async def _register_server_tools(self, server_info: MCPServerInfo):
        """Register tools from a connected server."""
        for tool in server_info.tools:
            tool_name = tool.get('name')
            if tool_name:
                # Check for name conflicts
                if tool_name in self.available_tools:
                    existing_server = self.available_tools[tool_name]
                    self.logger.warning(f"Tool name conflict: '{tool_name}' exists in both "
                                      f"{existing_server} and {server_info.server_id}")
                    # Use server-prefixed name
                    prefixed_name = f"{server_info.server_id}_{tool_name}"
                    self.available_tools[prefixed_name] = server_info.server_id
                else:
                    self.available_tools[tool_name] = server_info.server_id

                # Cache tool definition
                self.tool_cache[tool_name] = {
                    'server_id': server_info.server_id,
                    'endpoint': server_info.endpoint,
                    'definition': tool,
                    'last_used': None
                }

        self.logger.info(f"Registered {len(server_info.tools)} tools from {server_info.server_id}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a tool from any connected MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution results
        """
        if tool_name not in self.available_tools:
            return {
                'success': False,
                'error': f'Tool "{tool_name}" not available',
                'available_tools': list(self.available_tools.keys())
            }

        server_id = self.available_tools[tool_name]
        server_info = self.servers[server_id]

        if server_info.status != 'connected':
            # Try to reconnect
            if self.auto_reconnect:
                reconnect_result = await self._reconnect_server(server_info)
                if not reconnect_result['success']:
                    return {
                        'success': False,
                        'error': f'Server {server_id} not connected and reconnection failed',
                        'reconnect_error': reconnect_result.get('error')
                    }

        try:
            # Call the tool via base client
            result = await self.base_client.call_tool(
                server_info.endpoint,
                tool_name,
                arguments or {}
            )

            # Update tool cache
            if tool_name in self.tool_cache:
                self.tool_cache[tool_name]['last_used'] = datetime.now()

            # Reset error count on successful call
            server_info.error_count = 0

            return {
                'success': True,
                'tool_name': tool_name,
                'server_id': server_id,
                'result': result
            }

        except Exception as e:
            # Increment error count
            server_info.error_count += 1

            if server_info.error_count >= server_info.max_errors:
                server_info.status = 'error'
                self.logger.error(f"Server {server_id} marked as error after {server_info.error_count} failures")

            self.logger.error(f"Tool call failed for {tool_name} on {server_id}: {e}")

            return {
                'success': False,
                'error': str(e),
                'tool_name': tool_name,
                'server_id': server_id,
                'error_count': server_info.error_count
            }

    async def get_available_tools(self) -> Dict[str, Any]:
        """Get list of all available tools across all servers."""
        tools_by_server = {}

        for tool_name, server_id in self.available_tools.items():
            if server_id not in tools_by_server:
                tools_by_server[server_id] = []

            tools_by_server[server_id].append({
                'name': tool_name,
                'definition': self.tool_cache.get(tool_name, {}).get('definition', {}),
                'last_used': self.tool_cache.get(tool_name, {}).get('last_used')
            })

        return {
            'total_tools': len(self.available_tools),
            'servers': len(self.servers),
            'connected_servers': len([s for s in self.servers.values() if s.status == 'connected']),
            'tools_by_server': tools_by_server,
            'tool_list': list(self.available_tools.keys())
        }

    async def _health_monitor_loop(self):
        """Background health monitoring for connected servers."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval.total_seconds())

                if not self.servers:
                    continue

                self.logger.debug("Running health checks on MCP servers")

                health_tasks = [
                    self._health_check_server(server_info)
                    for server_info in self.servers.values()
                ]

                await asyncio.gather(*health_tasks, return_exceptions=True)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")

    async def _health_check_server(self, server_info: MCPServerInfo):
        """Perform health check on a single server."""
        try:
            if server_info.status == 'connected':
                # Try a simple list_tools call to check health
                result = await self.base_client.list_tools(server_info.endpoint)

                if result:
                    server_info.last_health_check = datetime.now()
                    server_info.error_count = 0
                else:
                    server_info.error_count += 1

            elif server_info.status == 'error' and self.auto_reconnect:
                # Try to reconnect failed servers
                await self._reconnect_server(server_info)

        except Exception as e:
            server_info.error_count += 1
            self.logger.debug(f"Health check failed for {server_info.server_id}: {e}")

            if server_info.error_count >= server_info.max_errors:
                server_info.status = 'error'

    async def _reconnect_server(self, server_info: MCPServerInfo) -> Dict[str, Any]:
        """Attempt to reconnect to a failed server."""
        if server_info.connection_attempts >= server_info.max_connection_attempts:
            return {
                'success': False,
                'error': 'Maximum connection attempts exceeded'
            }

        server_info.connection_attempts += 1
        server_info.status = 'connecting'

        try:
            connected = await self.base_client.connect(server_info.endpoint)

            if connected:
                server_info.status = 'connected'
                server_info.error_count = 0
                server_info.connection_attempts = 0
                server_info.last_health_check = datetime.now()

                # Re-register tools
                await self._register_server_tools(server_info)

                self.logger.info(f"Successfully reconnected to {server_info.server_id}")
                return {'success': True}
            else:
                server_info.status = 'error'
                return {'success': False, 'error': 'Connection failed'}

        except Exception as e:
            server_info.status = 'error'
            return {'success': False, 'error': str(e)}

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the MCP client system."""
        connected_servers = [s for s in self.servers.values() if s.status == 'connected']
        error_servers = [s for s in self.servers.values() if s.status == 'error']

        return {
            'client_status': 'operational',
            'discovery_enabled': self.discovery_enabled,
            'auto_reconnect': self.auto_reconnect,
            'last_discovery': self.last_discovery.isoformat() if self.last_discovery else None,
            'servers': {
                'total': len(self.servers),
                'connected': len(connected_servers),
                'error': len(error_servers),
                'connecting': len([s for s in self.servers.values() if s.status == 'connecting'])
            },
            'tools': {
                'total_available': len(self.available_tools),
                'cached_definitions': len(self.tool_cache)
            },
            'server_details': {
                server_id: {
                    'status': server.status,
                    'endpoint': server.endpoint,
                    'tools_count': len(server.tools),
                    'resources_count': len(server.resources),
                    'last_health_check': server.last_health_check.isoformat() if server.last_health_check else None,
                    'error_count': server.error_count
                }
                for server_id, server in self.servers.items()
            }
        }


# Export enhanced client instance
enhanced_mcp_client = EnhancedMCPClient()

async def initialize_mcp_client() -> Dict[str, Any]:
    """
    Initialize the enhanced MCP client.
    Claude Code compatible initialization function.
    """
    return await enhanced_mcp_client.initialize()

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call an MCP tool from any connected server.
    Claude Code compatible tool calling interface.
    """
    return await enhanced_mcp_client.call_tool(tool_name, arguments)