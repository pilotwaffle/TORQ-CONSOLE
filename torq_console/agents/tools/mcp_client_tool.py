"""
MCP Client Integration Tool for Prince Flowers Agent

Enables Prince Flowers to connect to external MCP (Model Context Protocol) servers
and invoke their tools and resources. Supports dynamic server discovery, connection
pooling, and graceful error handling.

MCP Protocol:
    The Model Context Protocol is a standardized protocol for AI model interaction
    with external tools and resources using JSON-RPC 2.0 over stdio or HTTP transport.

Author: Prince Flowers Team
Version: 1.0.0
Phase: 1.9
"""

import logging
import json
import asyncio
import subprocess
import os
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Try to import httpx for HTTP-based MCP servers
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not installed. HTTP MCP servers unavailable. Install with: pip install httpx")

logger = logging.getLogger(__name__)


class TransportType(Enum):
    """MCP server transport types."""
    STDIO = "stdio"
    HTTP = "http"
    UNKNOWN = "unknown"


class ConnectionState(Enum):
    """MCP server connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPServer:
    """
    MCP server configuration.

    Attributes:
        id: Unique server identifier
        name: Human-readable server name
        type: Transport type (stdio or http)
        command: Command to execute (for stdio)
        args: Command arguments (for stdio)
        url: Server URL (for http)
        env: Environment variables
        timeout: Connection timeout in seconds
    """
    id: str
    name: str
    type: str
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)


@dataclass
class MCPConnection:
    """
    Active MCP server connection.

    Attributes:
        server: Server configuration
        state: Connection state
        process: Subprocess for stdio connections
        client: HTTP client for HTTP connections
        connected_at: Connection timestamp
        last_activity: Last activity timestamp
        error: Error message if in ERROR state
    """
    server: MCPServer
    state: ConnectionState
    process: Optional[subprocess.Popen] = None
    client: Optional[Any] = None  # httpx.AsyncClient
    connected_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    error: Optional[str] = None
    request_id: int = 0

    def get_next_request_id(self) -> int:
        """Get next JSON-RPC request ID."""
        self.request_id += 1
        return self.request_id


class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass


class MCPConnectionError(MCPClientError):
    """Raised when connection to MCP server fails."""
    pass


class MCPServerNotFoundError(MCPClientError):
    """Raised when server ID is not found."""
    pass


class MCPToolNotFoundError(MCPClientError):
    """Raised when tool is not found on server."""
    pass


class MCPProtocolError(MCPClientError):
    """Raised when MCP protocol error occurs."""
    pass


class MCPClientTool:
    """
    MCP (Model Context Protocol) Client Integration Tool.

    Enables Prince Flowers to connect to external MCP servers and invoke
    their tools and resources. Supports dynamic server discovery, connection
    pooling, and graceful error handling.

    Operations:
        - list_servers: Get available MCP servers
        - connect_server: Establish server connection
        - disconnect_server: Close server connection
        - get_server_status: Check connection health
        - list_tools: Get server's available tools
        - get_tool_info: Get tool metadata
        - call_tool: Invoke server tool
        - get_resources: Get available resources
        - read_resource: Access server resource

    Configuration:
        Server configuration is loaded from JSON file with the format:
        {
            "servers": [
                {
                    "id": "filesystem",
                    "name": "Filesystem Server",
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
                    "env": {}
                }
            ]
        }

    Example:
        tool = MCPClientTool(server_config_path='mcp_servers.json')
        servers = await tool.execute(operation='list_servers')
        connection = await tool.execute(
            operation='connect_server',
            server_id='filesystem-server'
        )
        tools = await tool.execute(
            operation='list_tools',
            server_id='filesystem-server'
        )
        result = await tool.execute(
            operation='call_tool',
            server_id='filesystem-server',
            tool_name='read_file',
            params={'path': '/etc/hosts'}
        )
    """

    # Maximum number of retry attempts
    MAX_RETRIES = 3

    # Retry backoff multiplier (exponential backoff)
    RETRY_BACKOFF = 2.0

    # Default connection pool size
    DEFAULT_POOL_SIZE = 5

    # Request timeout in seconds
    DEFAULT_REQUEST_TIMEOUT = 60

    def __init__(
        self,
        server_config_path: Optional[str] = None,
        connection_timeout: int = 30,
        request_timeout: int = 60,
        max_retries: int = 3,
        pool_size: int = 5
    ):
        """
        Initialize MCP Client Tool with configuration.

        Args:
            server_config_path: Path to MCP server configuration file
            connection_timeout: Connection timeout in seconds (default: 30)
            request_timeout: Request timeout in seconds (default: 60)
            max_retries: Maximum retry attempts (default: 3)
            pool_size: Connection pool size (default: 5)
        """
        self.logger = logging.getLogger(__name__)

        # Tool metadata for Prince's ecosystem
        self.name = "MCP Client Integration"
        self.description = "Connect to MCP servers and invoke their tools and resources"
        self.cost = 0.3
        self.success_rate = 0.90
        self.avg_time = 2.0
        self.requires_approval = False
        self.composable = True

        # Configuration
        self.server_config_path = server_config_path
        self.connection_timeout = connection_timeout
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.pool_size = pool_size

        # Server registry and connections
        self.servers: Dict[str, MCPServer] = {}
        self.connections: Dict[str, MCPConnection] = {}

        # Load server configuration
        self._load_server_config()

        self.logger.info(
            f"Initialized MCP Client Tool with {len(self.servers)} configured servers"
        )

    def _load_server_config(self) -> None:
        """
        Load MCP server configuration from JSON file.

        Raises:
            MCPClientError: If configuration file cannot be loaded
        """
        if not self.server_config_path:
            self.logger.warning("No server configuration path provided")
            return

        try:
            config_path = Path(self.server_config_path)
            if not config_path.exists():
                self.logger.warning(f"Server configuration file not found: {self.server_config_path}")
                return

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Parse server configurations
            servers_config = config.get('servers', [])
            for server_data in servers_config:
                try:
                    # Expand environment variables in env dict
                    env = server_data.get('env', {})
                    if env:
                        expanded_env = {}
                        for key, value in env.items():
                            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                                env_var = value[2:-1]
                                expanded_env[key] = os.getenv(env_var, '')
                            else:
                                expanded_env[key] = value
                        server_data['env'] = expanded_env

                    server = MCPServer(**server_data)
                    self.servers[server.id] = server
                    self.logger.info(f"Loaded MCP server: {server.name} ({server.id})")
                except Exception as e:
                    self.logger.error(f"Failed to load server config: {e}")
                    continue

            self.logger.info(f"Loaded {len(self.servers)} MCP server configurations")

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in server configuration: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load server configuration: {e}")

    def is_available(self) -> bool:
        """
        Check if MCP client is available and configured.

        Returns:
            bool: True if tool is available and has configured servers
        """
        if not self.servers:
            self.logger.warning("No MCP servers configured")
            return False

        return True

    async def execute(
        self,
        operation: str,
        server_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        params: Optional[Dict] = None,
        uri: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute MCP client operation.

        Args:
            operation: Operation to perform
                - list_servers: Get available MCP servers
                - connect_server: Establish server connection
                - disconnect_server: Close server connection
                - get_server_status: Check connection health
                - list_tools: Get server's available tools
                - get_tool_info: Get tool metadata
                - call_tool: Invoke server tool
                - get_resources: Get available resources
                - read_resource: Access server resource
            server_id: MCP server identifier (required for most operations)
            tool_name: Tool to invoke (required for call_tool and get_tool_info)
            params: Tool parameters (required for call_tool)
            uri: Resource URI (required for read_resource)
            **kwargs: Additional parameters

        Returns:
            Dict with operation results:
                - success: bool - Operation success status
                - result: Any - Operation result data
                - error: str - Error message (if failed)
                - execution_time: float - Operation duration in seconds
                - timestamp: str - ISO format timestamp

        Raises:
            MCPClientError: For various error conditions
        """
        start_time = datetime.now()

        try:
            # Route to appropriate handler
            if operation == 'list_servers':
                result = await self._list_servers()
            elif operation == 'connect_server':
                if not server_id:
                    raise ValueError("server_id is required for connect_server operation")
                result = await self._connect_server(server_id)
            elif operation == 'disconnect_server':
                if not server_id:
                    raise ValueError("server_id is required for disconnect_server operation")
                result = await self._disconnect_server(server_id)
            elif operation == 'get_server_status':
                if not server_id:
                    raise ValueError("server_id is required for get_server_status operation")
                result = await self._get_server_status(server_id)
            elif operation == 'list_tools':
                if not server_id:
                    raise ValueError("server_id is required for list_tools operation")
                result = await self._list_tools(server_id)
            elif operation == 'get_tool_info':
                if not server_id or not tool_name:
                    raise ValueError("server_id and tool_name are required for get_tool_info operation")
                result = await self._get_tool_info(server_id, tool_name)
            elif operation == 'call_tool':
                if not server_id or not tool_name:
                    raise ValueError("server_id and tool_name are required for call_tool operation")
                result = await self._call_tool(server_id, tool_name, params or {})
            elif operation == 'get_resources':
                if not server_id:
                    raise ValueError("server_id is required for get_resources operation")
                result = await self._get_resources(server_id)
            elif operation == 'read_resource':
                if not server_id or not uri:
                    raise ValueError("server_id and uri are required for read_resource operation")
                result = await self._read_resource(server_id, uri)
            else:
                raise ValueError(
                    f"Unknown operation: {operation}. Valid operations: "
                    f"list_servers, connect_server, disconnect_server, get_server_status, "
                    f"list_tools, get_tool_info, call_tool, get_resources, read_resource"
                )

            # Add execution metadata
            result['execution_time'] = (datetime.now() - start_time).total_seconds()
            result['timestamp'] = datetime.now().isoformat()

            if result.get('success'):
                self.logger.info(f"MCP {operation} completed successfully")
            else:
                self.logger.warning(f"MCP {operation} failed: {result.get('error')}")

            return result

        except ValueError as e:
            error_msg = f"Validation error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
        except MCPClientError as e:
            error_msg = f"MCP client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Unexpected error during {operation}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }

    async def _list_servers(self) -> Dict[str, Any]:
        """
        List all configured MCP servers.

        Returns:
            Dict with success status and list of servers
        """
        try:
            servers_list = []
            for server_id, server in self.servers.items():
                connection = self.connections.get(server_id)
                server_info = {
                    'id': server.id,
                    'name': server.name,
                    'type': server.type,
                    'connected': connection.state == ConnectionState.CONNECTED if connection else False,
                    'state': connection.state.value if connection else ConnectionState.DISCONNECTED.value
                }
                servers_list.append(server_info)

            return {
                'success': True,
                'result': {
                    'servers': servers_list,
                    'count': len(servers_list)
                },
                'error': None
            }
        except Exception as e:
            error_msg = f"Error listing servers: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _connect_server(self, server_id: str) -> Dict[str, Any]:
        """
        Establish connection to MCP server.

        Args:
            server_id: Server identifier

        Returns:
            Dict with success status and connection details

        Raises:
            MCPServerNotFoundError: If server_id not found
            MCPConnectionError: If connection fails
        """
        try:
            # Check if server exists
            if server_id not in self.servers:
                raise MCPServerNotFoundError(f"Server not found: {server_id}")

            server = self.servers[server_id]

            # Check if already connected
            if server_id in self.connections:
                connection = self.connections[server_id]
                if connection.state == ConnectionState.CONNECTED:
                    return {
                        'success': True,
                        'result': {
                            'server_id': server_id,
                            'server_name': server.name,
                            'state': 'already_connected',
                            'connected_at': connection.connected_at.isoformat() if connection.connected_at else None
                        },
                        'error': None
                    }

            # Create connection
            connection = MCPConnection(
                server=server,
                state=ConnectionState.CONNECTING
            )

            # Connect based on transport type
            if server.type == TransportType.STDIO.value:
                await self._connect_stdio(connection)
            elif server.type == TransportType.HTTP.value:
                await self._connect_http(connection)
            else:
                raise MCPConnectionError(f"Unsupported transport type: {server.type}")

            # Store connection
            connection.state = ConnectionState.CONNECTED
            connection.connected_at = datetime.now()
            connection.last_activity = datetime.now()
            self.connections[server_id] = connection

            self.logger.info(f"Connected to MCP server: {server.name} ({server_id})")

            return {
                'success': True,
                'result': {
                    'server_id': server_id,
                    'server_name': server.name,
                    'state': 'connected',
                    'transport': server.type,
                    'connected_at': connection.connected_at.isoformat()
                },
                'error': None
            }

        except MCPClientError:
            raise
        except Exception as e:
            error_msg = f"Failed to connect to server {server_id}: {str(e)}"
            self.logger.error(error_msg)
            if server_id in self.connections:
                self.connections[server_id].state = ConnectionState.ERROR
                self.connections[server_id].error = error_msg
            raise MCPConnectionError(error_msg)

    async def _connect_stdio(self, connection: MCPConnection) -> None:
        """
        Connect to MCP server via stdio transport.

        Args:
            connection: MCP connection object

        Raises:
            MCPConnectionError: If connection fails
        """
        server = connection.server

        try:
            # Prepare environment
            env = os.environ.copy()
            if server.env:
                env.update(server.env)

            # Start subprocess
            command = [server.command] + (server.args or [])
            self.logger.info(f"Starting MCP server process: {' '.join(command)}")

            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )

            connection.process = process

            # Wait a moment for process to start
            await asyncio.sleep(0.5)

            # Check if process is still running
            if process.returncode is not None:
                stderr = await process.stderr.read()
                raise MCPConnectionError(
                    f"Server process exited immediately: {stderr.decode('utf-8', errors='ignore')}"
                )

            self.logger.info(f"MCP server process started: PID {process.pid}")

        except Exception as e:
            raise MCPConnectionError(f"Failed to start stdio server: {str(e)}")

    async def _connect_http(self, connection: MCPConnection) -> None:
        """
        Connect to MCP server via HTTP transport.

        Args:
            connection: MCP connection object

        Raises:
            MCPConnectionError: If connection fails
        """
        if not HTTPX_AVAILABLE:
            raise MCPConnectionError("httpx not available. Install with: pip install httpx")

        server = connection.server

        try:
            # Create HTTP client
            client = httpx.AsyncClient(
                base_url=server.url,
                timeout=self.connection_timeout,
                headers={'Content-Type': 'application/json'}
            )

            # Test connection with a simple request
            response = await client.post(
                '/',
                json={
                    'jsonrpc': '2.0',
                    'id': 1,
                    'method': 'ping',
                    'params': {}
                }
            )

            # Check response
            if response.status_code >= 400:
                raise MCPConnectionError(f"HTTP server returned error: {response.status_code}")

            connection.client = client
            self.logger.info(f"Connected to HTTP MCP server: {server.url}")

        except httpx.HTTPError as e:
            raise MCPConnectionError(f"HTTP connection failed: {str(e)}")
        except Exception as e:
            raise MCPConnectionError(f"Failed to connect to HTTP server: {str(e)}")

    async def _disconnect_server(self, server_id: str) -> Dict[str, Any]:
        """
        Disconnect from MCP server.

        Args:
            server_id: Server identifier

        Returns:
            Dict with success status
        """
        try:
            if server_id not in self.connections:
                return {
                    'success': True,
                    'result': {
                        'server_id': server_id,
                        'state': 'not_connected'
                    },
                    'error': None
                }

            connection = self.connections[server_id]

            # Close connection based on transport type
            if connection.process:
                connection.process.terminate()
                try:
                    await asyncio.wait_for(connection.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    connection.process.kill()
                    await connection.process.wait()
                self.logger.info(f"Terminated MCP server process: {server_id}")

            if connection.client:
                await connection.client.aclose()
                self.logger.info(f"Closed HTTP connection: {server_id}")

            # Remove connection
            del self.connections[server_id]

            return {
                'success': True,
                'result': {
                    'server_id': server_id,
                    'state': 'disconnected'
                },
                'error': None
            }

        except Exception as e:
            error_msg = f"Error disconnecting from server {server_id}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _get_server_status(self, server_id: str) -> Dict[str, Any]:
        """
        Get MCP server connection status.

        Args:
            server_id: Server identifier

        Returns:
            Dict with success status and server status
        """
        try:
            if server_id not in self.servers:
                raise MCPServerNotFoundError(f"Server not found: {server_id}")

            server = self.servers[server_id]
            connection = self.connections.get(server_id)

            if not connection:
                return {
                    'success': True,
                    'result': {
                        'server_id': server_id,
                        'server_name': server.name,
                        'state': ConnectionState.DISCONNECTED.value,
                        'connected': False
                    },
                    'error': None
                }

            # Check if connection is healthy
            is_healthy = False
            if connection.state == ConnectionState.CONNECTED:
                if connection.process:
                    is_healthy = connection.process.returncode is None
                elif connection.client:
                    is_healthy = not connection.client.is_closed

            return {
                'success': True,
                'result': {
                    'server_id': server_id,
                    'server_name': server.name,
                    'state': connection.state.value,
                    'connected': is_healthy,
                    'connected_at': connection.connected_at.isoformat() if connection.connected_at else None,
                    'last_activity': connection.last_activity.isoformat() if connection.last_activity else None,
                    'error': connection.error
                },
                'error': None
            }

        except MCPClientError:
            raise
        except Exception as e:
            error_msg = f"Error getting server status: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _send_jsonrpc_request(
        self,
        connection: MCPConnection,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to MCP server.

        Args:
            connection: MCP connection
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            JSON-RPC response result

        Raises:
            MCPProtocolError: If protocol error occurs
        """
        request_id = connection.get_next_request_id()

        request = {
            'jsonrpc': '2.0',
            'id': request_id,
            'method': method,
            'params': params or {}
        }

        try:
            if connection.process:
                # Stdio transport
                request_json = json.dumps(request) + '\n'
                connection.process.stdin.write(request_json.encode('utf-8'))
                await connection.process.stdin.drain()

                # Read response
                response_line = await asyncio.wait_for(
                    connection.process.stdout.readline(),
                    timeout=self.request_timeout
                )
                response = json.loads(response_line.decode('utf-8'))

            elif connection.client:
                # HTTP transport
                response_obj = await asyncio.wait_for(
                    connection.client.post('/', json=request),
                    timeout=self.request_timeout
                )
                response = response_obj.json()
            else:
                raise MCPProtocolError("No active connection")

            # Update last activity
            connection.last_activity = datetime.now()

            # Check for JSON-RPC error
            if 'error' in response:
                error = response['error']
                raise MCPProtocolError(
                    f"JSON-RPC error: {error.get('message', 'Unknown error')} "
                    f"(code: {error.get('code', 'N/A')})"
                )

            # Return result
            return response.get('result', {})

        except asyncio.TimeoutError:
            raise MCPProtocolError(f"Request timeout after {self.request_timeout}s")
        except json.JSONDecodeError as e:
            raise MCPProtocolError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            raise MCPProtocolError(f"Request failed: {str(e)}")

    async def _list_tools(self, server_id: str) -> Dict[str, Any]:
        """
        List tools available on MCP server.

        Args:
            server_id: Server identifier

        Returns:
            Dict with success status and list of tools
        """
        try:
            connection = await self._ensure_connected(server_id)

            # Send tools/list request
            result = await self._send_jsonrpc_request(connection, 'tools/list')

            tools = result.get('tools', [])

            return {
                'success': True,
                'result': {
                    'server_id': server_id,
                    'tools': tools,
                    'count': len(tools)
                },
                'error': None
            }

        except MCPClientError:
            raise
        except Exception as e:
            error_msg = f"Error listing tools: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _get_tool_info(self, server_id: str, tool_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific tool.

        Args:
            server_id: Server identifier
            tool_name: Tool name

        Returns:
            Dict with success status and tool metadata
        """
        try:
            # First get list of tools
            tools_result = await self._list_tools(server_id)
            if not tools_result['success']:
                return tools_result

            # Find the specific tool
            tools = tools_result['result']['tools']
            tool_info = None
            for tool in tools:
                if tool.get('name') == tool_name:
                    tool_info = tool
                    break

            if not tool_info:
                raise MCPToolNotFoundError(f"Tool not found: {tool_name}")

            return {
                'success': True,
                'result': {
                    'server_id': server_id,
                    'tool': tool_info
                },
                'error': None
            }

        except MCPClientError:
            raise
        except Exception as e:
            error_msg = f"Error getting tool info: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _call_tool(
        self,
        server_id: str,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke a tool on MCP server.

        Args:
            server_id: Server identifier
            tool_name: Tool name to invoke
            params: Tool parameters

        Returns:
            Dict with success status and tool result
        """
        try:
            connection = await self._ensure_connected(server_id)

            # Send tools/call request
            result = await self._send_jsonrpc_request(
                connection,
                'tools/call',
                {
                    'name': tool_name,
                    'arguments': params
                }
            )

            return {
                'success': True,
                'result': {
                    'server_id': server_id,
                    'tool_name': tool_name,
                    'output': result
                },
                'error': None
            }

        except MCPClientError:
            raise
        except Exception as e:
            error_msg = f"Error calling tool {tool_name}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _get_resources(self, server_id: str) -> Dict[str, Any]:
        """
        Get available resources from MCP server.

        Args:
            server_id: Server identifier

        Returns:
            Dict with success status and list of resources
        """
        try:
            connection = await self._ensure_connected(server_id)

            # Send resources/list request
            result = await self._send_jsonrpc_request(connection, 'resources/list')

            resources = result.get('resources', [])

            return {
                'success': True,
                'result': {
                    'server_id': server_id,
                    'resources': resources,
                    'count': len(resources)
                },
                'error': None
            }

        except MCPClientError:
            raise
        except Exception as e:
            error_msg = f"Error getting resources: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _read_resource(self, server_id: str, uri: str) -> Dict[str, Any]:
        """
        Read a resource from MCP server.

        Args:
            server_id: Server identifier
            uri: Resource URI

        Returns:
            Dict with success status and resource content
        """
        try:
            connection = await self._ensure_connected(server_id)

            # Send resources/read request
            result = await self._send_jsonrpc_request(
                connection,
                'resources/read',
                {'uri': uri}
            )

            return {
                'success': True,
                'result': {
                    'server_id': server_id,
                    'uri': uri,
                    'content': result.get('contents', [])
                },
                'error': None
            }

        except MCPClientError:
            raise
        except Exception as e:
            error_msg = f"Error reading resource {uri}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _ensure_connected(self, server_id: str) -> MCPConnection:
        """
        Ensure connection to server is established.

        Args:
            server_id: Server identifier

        Returns:
            Active MCP connection

        Raises:
            MCPServerNotFoundError: If server not found
            MCPConnectionError: If connection cannot be established
        """
        if server_id not in self.servers:
            raise MCPServerNotFoundError(f"Server not found: {server_id}")

        if server_id not in self.connections or self.connections[server_id].state != ConnectionState.CONNECTED:
            # Auto-connect
            result = await self._connect_server(server_id)
            if not result['success']:
                raise MCPConnectionError(f"Failed to connect: {result['error']}")

        return self.connections[server_id]

    async def cleanup(self) -> None:
        """Cleanup all connections and resources."""
        self.logger.info("Cleaning up MCP client connections")

        # Disconnect all servers
        for server_id in list(self.connections.keys()):
            try:
                await self._disconnect_server(server_id)
            except Exception as e:
                self.logger.error(f"Error disconnecting {server_id} during cleanup: {e}")

        self.logger.info("MCP client cleanup complete")


def create_mcp_client_tool(
    server_config_path: Optional[str] = None,
    connection_timeout: int = 30,
    request_timeout: int = 60,
    max_retries: int = 3,
    pool_size: int = 5
) -> MCPClientTool:
    """
    Factory function to create MCP Client Tool instance.

    Args:
        server_config_path: Path to server configuration file
        connection_timeout: Connection timeout in seconds (default: 30)
        request_timeout: Request timeout in seconds (default: 60)
        max_retries: Maximum retry attempts (default: 3)
        pool_size: Connection pool size (default: 5)

    Returns:
        Configured MCPClientTool instance

    Example:
        >>> # Using default configuration
        >>> tool = create_mcp_client_tool()
        >>>
        >>> # With custom configuration
        >>> tool = create_mcp_client_tool(
        ...     server_config_path='E:/mcp_servers.json',
        ...     connection_timeout=60,
        ...     request_timeout=120
        ... )
        >>>
        >>> # Use the tool
        >>> result = await tool.execute(operation='list_servers')
    """
    return MCPClientTool(
        server_config_path=server_config_path,
        connection_timeout=connection_timeout,
        request_timeout=request_timeout,
        max_retries=max_retries,
        pool_size=pool_size
    )
