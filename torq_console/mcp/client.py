"""
MCP Client for TORQ CONSOLE.

Provides a comprehensive client for connecting to and interacting with
Model Context Protocol (MCP) servers.
"""

import asyncio
import json
import logging
import subprocess
import uuid
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import httpx

from jsonrpcclient import request, parse, Ok, Error


class MCPClient:
    """
    MCP (Model Context Protocol) client for TORQ CONSOLE.

    Supports both stdio and HTTP transports for connecting to MCP servers
    and provides a unified interface for tool calls, resource access, and prompts.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, Any] = {}
        self.server_info: Dict[str, Any] = {}

    async def connect(self, endpoint: str) -> bool:
        """
        Connect to an MCP server.

        Args:
            endpoint: Server endpoint (stdio://path or http://url)

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if endpoint.startswith("stdio://"):
                return await self._connect_stdio(endpoint)
            elif endpoint.startswith("http://") or endpoint.startswith("https://"):
                return await self._connect_http(endpoint)
            else:
                self.logger.error(f"Unsupported endpoint format: {endpoint}")
                return False

        except Exception as e:
            self.logger.error(f"Connection to {endpoint} failed: {e}")
            return False

    async def _connect_stdio(self, endpoint: str) -> bool:
        """Connect to stdio-based MCP server."""
        try:
            # Extract command from endpoint
            command_path = endpoint[8:]  # Remove "stdio://"

            # Start the subprocess
            process = await asyncio.create_subprocess_exec(
                "python", "-m", command_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            if process.returncode is not None:
                self.logger.error(f"Failed to start stdio server: {command_path}")
                return False

            # Store connection
            self.connections[endpoint] = {
                "type": "stdio",
                "process": process,
                "endpoint": endpoint
            }

            # Initialize the server
            success = await self._initialize_server(endpoint)
            if not success:
                await self.disconnect(endpoint)
                return False

            self.logger.info(f"Connected to stdio server: {endpoint}")
            return True

        except Exception as e:
            self.logger.error(f"Stdio connection error: {e}")
            return False

    async def _connect_http(self, endpoint: str) -> bool:
        """Connect to HTTP-based MCP server."""
        try:
            # Test connection with a simple request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    endpoint,
                    json=request("initialize", {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "roots": {"listChanged": True},
                            "sampling": {}
                        },
                        "clientInfo": {
                            "name": "TORQ CONSOLE",
                            "version": "0.70.0"
                        }
                    }),
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    self.logger.error(f"HTTP server returned {response.status_code}")
                    return False

            # Store connection
            self.connections[endpoint] = {
                "type": "http",
                "endpoint": endpoint
            }

            # Initialize the server
            success = await self._initialize_server(endpoint)
            if not success:
                await self.disconnect(endpoint)
                return False

            self.logger.info(f"Connected to HTTP server: {endpoint}")
            return True

        except Exception as e:
            self.logger.error(f"HTTP connection error: {e}")
            return False

    async def _initialize_server(self, endpoint: str) -> bool:
        """Initialize the MCP server connection."""
        try:
            # Send initialize request
            init_response = await self._send_request(endpoint, "initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "TORQ CONSOLE",
                    "version": "0.70.0"
                }
            })

            if not init_response:
                return False

            # Store server capabilities
            self.server_info[endpoint] = init_response

            # Send initialized notification
            await self._send_notification(endpoint, "notifications/initialized")

            return True

        except Exception as e:
            self.logger.error(f"Server initialization error: {e}")
            return False

    async def disconnect(self, endpoint: str) -> bool:
        """Disconnect from an MCP server."""
        try:
            if endpoint not in self.connections:
                return True

            connection = self.connections[endpoint]

            if connection["type"] == "stdio":
                process = connection["process"]
                process.terminate()
                await process.wait()
            # HTTP connections don't need explicit cleanup

            del self.connections[endpoint]
            if endpoint in self.server_info:
                del self.server_info[endpoint]

            self.logger.info(f"Disconnected from {endpoint}")
            return True

        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
            return False

    async def list_tools(self, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available tools from the server."""
        try:
            # If no endpoint specified, use the first available
            if endpoint is None:
                if not self.connections:
                    return []
                endpoint = next(iter(self.connections.keys()))

            response = await self._send_request(endpoint, "tools/list")
            if response and "tools" in response:
                return response["tools"]

            return []

        except Exception as e:
            self.logger.error(f"Error listing tools: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None,
                       endpoint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Call a tool on the MCP server."""
        try:
            # If no endpoint specified, use the first available
            if endpoint is None:
                if not self.connections:
                    return None
                endpoint = next(iter(self.connections.keys()))

            if arguments is None:
                arguments = {}

            response = await self._send_request(endpoint, "tools/call", {
                "name": tool_name,
                "arguments": arguments
            })

            return response

        except Exception as e:
            self.logger.error(f"Error calling tool {tool_name}: {e}")
            return None

    async def list_resources(self, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available resources from the server."""
        try:
            if endpoint is None:
                if not self.connections:
                    return []
                endpoint = next(iter(self.connections.keys()))

            response = await self._send_request(endpoint, "resources/list")
            if response and "resources" in response:
                return response["resources"]

            return []

        except Exception as e:
            self.logger.error(f"Error listing resources: {e}")
            return []

    async def read_resource(self, uri: str, endpoint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Read a resource from the server."""
        try:
            if endpoint is None:
                if not self.connections:
                    return None
                endpoint = next(iter(self.connections.keys()))

            response = await self._send_request(endpoint, "resources/read", {
                "uri": uri
            })

            return response

        except Exception as e:
            self.logger.error(f"Error reading resource {uri}: {e}")
            return None

    async def list_prompts(self, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available prompts from the server."""
        try:
            if endpoint is None:
                if not self.connections:
                    return []
                endpoint = next(iter(self.connections.keys()))

            response = await self._send_request(endpoint, "prompts/list")
            if response and "prompts" in response:
                return response["prompts"]

            return []

        except Exception as e:
            self.logger.error(f"Error listing prompts: {e}")
            return []

    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None,
                        endpoint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a prompt from the server."""
        try:
            if endpoint is None:
                if not self.connections:
                    return None
                endpoint = next(iter(self.connections.keys()))

            if arguments is None:
                arguments = {}

            response = await self._send_request(endpoint, "prompts/get", {
                "name": name,
                "arguments": arguments
            })

            return response

        except Exception as e:
            self.logger.error(f"Error getting prompt {name}: {e}")
            return None

    async def get_server_info(self, endpoint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get server information."""
        if endpoint is None:
            if not self.connections:
                return None
            endpoint = next(iter(self.connections.keys()))

        return self.server_info.get(endpoint)

    async def _send_request(self, endpoint: str, method: str,
                           params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request to the server."""
        try:
            if endpoint not in self.connections:
                self.logger.error(f"No connection to {endpoint}")
                return None

            connection = self.connections[endpoint]

            if params is None:
                params = {}

            # Generate request ID
            request_id = str(uuid.uuid4())

            if connection["type"] == "stdio":
                return await self._send_stdio_request(connection, method, params, request_id)
            elif connection["type"] == "http":
                return await self._send_http_request(connection, method, params, request_id)

        except Exception as e:
            self.logger.error(f"Request error: {e}")
            return None

    async def _send_stdio_request(self, connection: Dict[str, Any], method: str,
                                 params: Dict[str, Any], request_id: str) -> Optional[Dict[str, Any]]:
        """Send request via stdio transport."""
        try:
            process = connection["process"]

            # Prepare JSON-RPC request
            rpc_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params
            }

            # Send request
            request_data = json.dumps(rpc_request) + "\n"
            process.stdin.write(request_data.encode())
            await process.stdin.drain()

            # Read response
            response_line = await process.stdout.readline()
            if not response_line:
                return None

            response_data = json.loads(response_line.decode().strip())

            if "error" in response_data:
                self.logger.error(f"Server error: {response_data['error']}")
                return None

            return response_data.get("result")

        except Exception as e:
            self.logger.error(f"Stdio request error: {e}")
            return None

    async def _send_http_request(self, connection: Dict[str, Any], method: str,
                                params: Dict[str, Any], request_id: str) -> Optional[Dict[str, Any]]:
        """Send request via HTTP transport."""
        try:
            endpoint = connection["endpoint"]

            # Prepare JSON-RPC request
            rpc_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    json=rpc_request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    self.logger.error(f"HTTP error: {response.status_code}")
                    return None

                response_data = response.json()

                if "error" in response_data:
                    self.logger.error(f"Server error: {response_data['error']}")
                    return None

                return response_data.get("result")

        except Exception as e:
            self.logger.error(f"HTTP request error: {e}")
            return None

    async def _send_notification(self, endpoint: str, method: str,
                                params: Dict[str, Any] = None):
        """Send a notification (no response expected)."""
        try:
            if endpoint not in self.connections:
                return

            connection = self.connections[endpoint]

            if params is None:
                params = {}

            # Prepare JSON-RPC notification (no ID)
            rpc_notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params
            }

            if connection["type"] == "stdio":
                process = connection["process"]
                notification_data = json.dumps(rpc_notification) + "\n"
                process.stdin.write(notification_data.encode())
                await process.stdin.drain()

            elif connection["type"] == "http":
                endpoint_url = connection["endpoint"]
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        endpoint_url,
                        json=rpc_notification,
                        headers={"Content-Type": "application/json"}
                    )

        except Exception as e:
            self.logger.error(f"Notification error: {e}")

    def get_connected_endpoints(self) -> List[str]:
        """Get list of connected endpoints."""
        return list(self.connections.keys())

    def is_connected(self, endpoint: str) -> bool:
        """Check if connected to an endpoint."""
        return endpoint in self.connections

    async def health_check(self, endpoint: Optional[str] = None) -> bool:
        """Perform health check on server connection."""
        try:
            if endpoint is None:
                if not self.connections:
                    return False
                endpoint = next(iter(self.connections.keys()))

            # Try to list tools as a health check
            tools = await self.list_tools(endpoint)
            return tools is not None

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def shutdown(self):
        """Shutdown all connections."""
        for endpoint in list(self.connections.keys()):
            await self.disconnect(endpoint)

        self.logger.info("MCP client shutdown complete")